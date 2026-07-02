/**
 * WA gateway: bridges WhatsApp (via whatsapp-web.js) to the FastAPI /chat backend.
 *
 * - First run: scan the QR code printed in this terminal with WhatsApp
 *   (Linked devices -> Link a device). Session is cached locally after that.
 * - Debounces rapid-fire messages from the same chat so the bot replies once
 *   instead of spamming a reply per message.
 * - Auto-reconnects if the WhatsApp Web session drops.
 */
const path = require("path");
require("dotenv").config({ path: path.join(__dirname, "..", ".env") });

const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcodeTerminal = require("qrcode-terminal");
const qrcodeImage = require("qrcode");
const axios = require("axios");
const { shouldHandle, isHumanAdminReply, getChatId, isResumeCommand } = require("./lib");

const BACKEND_CHAT_URL = process.env.BACKEND_CHAT_URL || "http://localhost:8000/chat";
const BACKEND_HUMAN_REPLY_URL =
  process.env.BACKEND_HUMAN_REPLY_URL || BACKEND_CHAT_URL.replace(/\/chat$/, "/human-reply");
const BACKEND_RESUME_URL =
  process.env.BACKEND_RESUME_URL || BACKEND_CHAT_URL.replace(/\/chat$/, "/handoff/resume");
// Admin types this directly in the customer's chat to hand control back to the bot.
// Note: the customer will see this literal text too — WhatsApp has no hidden-command channel.
const RESUME_KEYWORD = process.env.WA_RESUME_KEYWORD || "/bot on";
const DEBOUNCE_MS = Number(process.env.WA_DEBOUNCE_MS || 3000);
const SESSION_DIR = process.env.WA_SESSION_DIR || "./.wwebjs_auth";
const RECONNECT_DELAY_MS = 5000;
// Optional: also dump the QR as a PNG (useful when the terminal can't render ASCII QR reliably).
const QR_IMAGE_PATH = process.env.WA_QR_IMAGE_PATH;

// Per-chat debounce state: chatId -> { timer, buffer: string[] }
const pending = new Map();

// "message_create" fires for every message the bot itself sends too (fromMe: true), same as
// a manual admin reply. Register the exact text we're about to send *synchronously, before*
// calling sendMessage/reply — matching on resolved message IDs would race against the
// "message_create" event, which can fire before our own .then() callback runs.
const ownOutgoingTexts = new Map(); // chatId -> text[] (list, not Set — handles duplicate replies)
function markOutgoing(chatId, text) {
  if (!ownOutgoingTexts.has(chatId)) ownOutgoingTexts.set(chatId, []);
  ownOutgoingTexts.get(chatId).push(text);
}
function consumeOutgoing(chatId, text) {
  const list = ownOutgoingTexts.get(chatId);
  if (!list) return false;
  const idx = list.indexOf(text);
  if (idx === -1) return false;
  list.splice(idx, 1);
  if (list.length === 0) ownOutgoingTexts.delete(chatId);
  return true;
}

// Serialize every outgoing sendMessage through one queue. Firing sendMessage concurrently
// (e.g. two debounce flushes for the same chat landing close together) can silently drop a
// message under memory/CPU pressure — Puppeteer evaluates run against the same page instance.
let sendQueue = Promise.resolve();
function queueSend(chatId, text) {
  markOutgoing(chatId, text);
  sendQueue = sendQueue
    .catch(() => {}) // don't let a prior failure poison the queue
    .then(() => client.sendMessage(chatId, text))
    .then((sent) => console.log(`Terkirim ke ${chatId}, message id: ${sent.id?._serialized}`));
  return sendQueue;
}

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: SESSION_DIR }),
  puppeteer: {
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  },
});

client.on("qr", (qr) => {
  console.log("Scan QR ini pake WhatsApp di HP lo (Linked devices > Link a device):");
  qrcodeTerminal.generate(qr, { small: true });
  if (QR_IMAGE_PATH) {
    qrcodeImage
      .toFile(QR_IMAGE_PATH, qr, { width: 400 })
      .then(() => console.log("QR juga disimpen sebagai gambar di:", QR_IMAGE_PATH))
      .catch((err) => console.error("Gagal simpen QR image:", err.message));
  }
});

client.on("ready", () => {
  console.log("WA gateway ready. Nomor terhubung:", client.info?.wid?.user);
});

client.on("auth_failure", (msg) => {
  console.error("Auth gagal:", msg);
});

client.on("disconnected", (reason) => {
  console.error(`WA disconnected (${reason}). Reconnecting in ${RECONNECT_DELAY_MS}ms...`);
  setTimeout(() => {
    client.initialize().catch((err) => console.error("Reconnect gagal:", err.message));
  }, RECONNECT_DELAY_MS);
});

// Cache phone resolution per chat — no need to re-resolve on every debounced message.
const phoneCache = new Map(); // chatId -> phone string | null

/** Real phone number behind a chat, for the dashboard's wa.me link. `@c.us` IDs already
 * are the number; `@lid` (privacy ID) needs a contact lookup, which can still fail to resolve. */
async function resolveCustomerPhone(chatId) {
  if (phoneCache.has(chatId)) return phoneCache.get(chatId);

  let phone = null;
  if (chatId.endsWith("@c.us")) {
    phone = chatId.split("@")[0];
  } else {
    try {
      const contact = await client.getContactById(chatId);
      phone = contact?.number || null;
    } catch (err) {
      console.error(`Gagal resolve nomor buat ${chatId}:`, err.message);
    }
  }

  phoneCache.set(chatId, phone);
  return phone;
}

async function forwardToBackend(sessionId, combinedMessage, customerPhone) {
  const response = await axios.post(
    BACKEND_CHAT_URL,
    { message: combinedMessage, session_id: sessionId, customer_phone: customerPhone },
    { timeout: 60000 },
  );
  return response.data; // { reply, bot_active, handoff, session_id }
}

/** Log a manual admin reply so /handoff/pending stops listing this session as bot-only. */
async function reportHumanReply(sessionId, content) {
  await axios.post(BACKEND_HUMAN_REPLY_URL, { session_id: sessionId, message: content }, { timeout: 10000 });
}

/** Admin typed the resume keyword — hand control back to the bot for this chat. */
async function resumeBot(sessionId) {
  await axios.post(BACKEND_RESUME_URL, { session_id: sessionId }, { timeout: 10000 });
}

async function flushChat(chatId) {
  const state = pending.get(chatId);
  if (!state) return;
  pending.delete(chatId);

  // Non-text messages (stickers, images without caption, reactions) have an empty body.
  // Skip forwarding those instead of hitting the backend's message min_length validation.
  const combinedMessage = state.buffer.filter((b) => b.trim().length > 0).join("\n");
  if (!combinedMessage) {
    console.log(`Skip ${chatId}: gak ada teks buat diproses (kemungkinan stiker/gambar/reaction).`);
    return;
  }

  try {
    const customerPhone = await resolveCustomerPhone(chatId);
    const data = await forwardToBackend(chatId, combinedMessage, customerPhone);
    if (!data.bot_active) {
      console.log(`Skip kirim ke ${chatId}: sesi lagi di-pause (admin nangani manual).`);
      return;
    }
    await queueSend(chatId, data.reply);
  } catch (err) {
    console.error(`Gagal proses pesan dari ${chatId}:`, err.message);
    await queueSend(
      chatId,
      "Waduh sori, sistemnya lagi error. Coba chat lagi bentar ya, atau tunggu admin bales manual.",
    ).catch(() => {});
  }
}

const FILE_RECEIVED_REPLY = "Filenya udah keterima ya kak, nanti dicek admin buat lanjut prosesnya 🙌";

// "message" skips fromMe messages entirely (whatsapp-web.js: `if (msg.id.fromMe) return;`
// before emitting it) — "message_create" fires for everything, including our own account's
// outgoing messages, which is what we need to detect the admin replying manually.
client.on("message_create", (message) => {
  // Our own bot-sent message, echoed back — not an admin reply.
  if (message.fromMe && consumeOutgoing(getChatId(message), message.body)) {
    return;
  }

  // Admin replied manually from their own phone/another linked device.
  if (isHumanAdminReply(message)) {
    const chatId = getChatId(message);

    if (isResumeCommand(message.body, RESUME_KEYWORD)) {
      resumeBot(chatId)
        .then(() => console.log(`Bot di-resume buat ${chatId}`))
        .catch((err) => console.error(`Gagal resume bot buat ${chatId}:`, err.message));
      return;
    }

    // Any other manual reply pauses the bot for this chat (see log_human_reply on the backend)
    // and shows up as human-handled in GET /handoff/pending.
    reportHumanReply(chatId, message.body || "(pesan non-teks)").catch((err) =>
      console.error(`Gagal log balasan admin ke ${chatId}:`, err.message),
    );
    return;
  }

  if (!shouldHandle(message)) return;

  // Images/documents/videos etc. — the bot can't "read" a design file or photo, so skip the
  // RAG/LLM pipeline entirely and just acknowledge receipt, quoting the message that had the file.
  if (message.hasMedia) {
    markOutgoing(getChatId(message), FILE_RECEIVED_REPLY);
    message
      .reply(FILE_RECEIVED_REPLY)
      .catch((err) => console.error(`Gagal reply media dari ${getChatId(message)}:`, err.message));
    return;
  }

  const chatId = getChatId(message);
  const existing = pending.get(chatId);

  if (existing) {
    clearTimeout(existing.timer);
    existing.buffer.push(message.body);
  } else {
    pending.set(chatId, { buffer: [message.body], timer: null });
  }

  const state = pending.get(chatId);
  state.timer = setTimeout(() => flushChat(chatId), DEBOUNCE_MS);
});

function shutdown() {
  console.log("Shutting down WA gateway...");
  client.destroy().finally(() => process.exit(0));
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

console.log("Starting WA gateway, backend:", BACKEND_CHAT_URL);
client.initialize();
