-- Telegram basic groups use negative (not necessarily -100) marked peer IDs.
-- This migration extends personal dialog selection without changing Bot identity policy.
ALTER TABLE telegram_personal_dialogs DROP CONSTRAINT IF EXISTS telegram_personal_dialogs_chat_id_check;
ALTER TABLE telegram_personal_dialogs
  ADD CONSTRAINT telegram_personal_dialogs_chat_id_check CHECK(chat_id ~ '^-?[0-9]{5,20}$');
