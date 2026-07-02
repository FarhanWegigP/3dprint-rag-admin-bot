/** Pure filtering logic, split out from index.js so it's testable without a live WA client. */

/**
 * The chat a message belongs to, regardless of direction. `message.from`/`message.to` flip
 * meaning depending on `fromMe` (for fromMe messages, `.from` is our own id, `.to` is the
 * chat) — `id.remote` is the WhatsApp protocol field that's always the chat JID.
 */
function getChatId(message) {
  return message.id.remote;
}

/** Only reply to normal 1:1 chats — skip groups, status broadcasts, and our own messages. */
function shouldHandle(message) {
  if (message.fromMe) return false;
  const chatId = getChatId(message);
  if (chatId === "status@broadcast") return false;
  if (chatId.endsWith("@g.us")) return false;
  return true;
}

/**
 * A `fromMe: true` message on the `message` event means the admin replied manually from
 * their own phone/another linked device (the bot's own sendMessage calls, made from this
 * same session, don't re-trigger this event). Same chat-type filtering as shouldHandle.
 */
function isHumanAdminReply(message) {
  if (!message.fromMe) return false;
  const chatId = getChatId(message);
  if (chatId === "status@broadcast") return false;
  if (chatId.endsWith("@g.us")) return false;
  return true;
}

/** Case/whitespace-insensitive match for the admin's "resume the bot" keyword. */
function isResumeCommand(body, keyword) {
  return (body || "").trim().toLowerCase() === keyword.trim().toLowerCase();
}

module.exports = { shouldHandle, isHumanAdminReply, getChatId, isResumeCommand };
