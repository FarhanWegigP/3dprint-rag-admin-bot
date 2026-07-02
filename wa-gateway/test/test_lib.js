// Self-check for the message-filtering logic. Run: node test/test_lib.js
const assert = require("node:assert");
const { shouldHandle, isHumanAdminReply, getChatId, isResumeCommand } = require("../lib");

function msg({ fromMe, remote }) {
  return { fromMe, id: { remote } };
}

// shouldHandle — bot's auto-reply gate (incoming customer messages only)
assert.strictEqual(shouldHandle(msg({ fromMe: true, remote: "628@c.us" })), false, "should skip own messages");
assert.strictEqual(shouldHandle(msg({ fromMe: false, remote: "status@broadcast" })), false, "should skip status broadcast");
assert.strictEqual(shouldHandle(msg({ fromMe: false, remote: "12345-6789@g.us" })), false, "should skip groups");
assert.strictEqual(shouldHandle(msg({ fromMe: false, remote: "6281234567890@c.us" })), true, "should handle normal 1:1 chat");

// isHumanAdminReply — detects the admin manually replying from their own phone
assert.strictEqual(isHumanAdminReply(msg({ fromMe: false, remote: "6281234567890@c.us" })), false, "customer messages are not admin replies");
assert.strictEqual(isHumanAdminReply(msg({ fromMe: true, remote: "status@broadcast" })), false, "should skip status broadcast");
assert.strictEqual(isHumanAdminReply(msg({ fromMe: true, remote: "12345-6789@g.us" })), false, "should skip groups");
assert.strictEqual(isHumanAdminReply(msg({ fromMe: true, remote: "6281234567890@c.us" })), true, "should detect manual 1:1 admin reply");

// getChatId always resolves to the chat JID, not the sender
assert.strictEqual(getChatId(msg({ fromMe: true, remote: "6281234567890@c.us" })), "6281234567890@c.us");

// isResumeCommand — case/whitespace-insensitive match against the configured keyword
assert.strictEqual(isResumeCommand("/bot on", "/bot on"), true);
assert.strictEqual(isResumeCommand("  /BOT ON  ", "/bot on"), true, "should be case/whitespace-insensitive");
assert.strictEqual(isResumeCommand("bot on please", "/bot on"), false, "should require exact match, not substring");
assert.strictEqual(isResumeCommand("", "/bot on"), false);
assert.strictEqual(isResumeCommand(undefined, "/bot on"), false);

console.log("OK - all wa-gateway lib checks passed");
