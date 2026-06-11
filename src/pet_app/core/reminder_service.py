"""Reminder service for todo DDL notifications."""

from datetime import datetime
from typing import Optional, Callable, Dict, Any, Tuple
from pet_app.core.todo_service import TodoService
from pet_app.core.ai_client import AIClient
from pet_app.core.reminder_config import REMINDER_KEYWORDS, get_forbidden_words_prompt, contains_forbidden_word
from pet_app.utils.logger import logger


class ReminderService:
    """Handle todo DDL reminders and AI notifications."""

    def __init__(self, todo_service: TodoService, ai_client: AIClient):
        """Initialize reminder service."""
        self.todo_service = todo_service
        self.ai_client = ai_client
        self.on_reminder_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        logger.info("ReminderService initialized")

    def set_on_reminder_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback for when a reminder should be displayed."""
        self.on_reminder_callback = callback

    def _find_category_and_examples(self, title: str, description: str, reminder_type: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Find matching category and example replies for this todo."""
        content = f"{title} {description}".lower()

        for category, config in REMINDER_KEYWORDS.items():
            keywords = config.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in content:
                    examples = config.get(reminder_type, {})
                    if examples:
                        return category, examples
                    break

        return None, None

    def scan_reminders(self) -> bool:
        """Scan todos and trigger reminders if needed. Returns True if reminder was triggered."""
        try:
            todos = self.todo_service.get_pending_todos()
            now = datetime.now()

            logger.debug(f"[Reminder] Scanning {len(todos)} pending todos at {now.strftime('%H:%M:%S')}")

            reminder_todo = None
            reminder_type = None

            for todo in todos:
                if not todo.ddl:
                    logger.debug(f"[Reminder] Todo {todo.id} ({todo.title}) has no DDL, skip")
                    continue

                try:
                    ddl_time = datetime.strptime(todo.ddl, "%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    logger.warning(f"[Reminder] Invalid DDL format for todo {todo.id}: {todo.ddl}")
                    continue

                if ddl_time <= now:
                    logger.debug(f"[Reminder] Todo {todo.id} ({todo.title}) DDL expired at {todo.ddl}, skip")
                    continue

                time_diff = (ddl_time - now).total_seconds()
                hours_left = time_diff / 3600
                minutes_left = time_diff / 60

                logger.debug(f"[Reminder] Todo {todo.id} ({todo.title}): {hours_left:.1f}h left, one_day={todo.reminded_one_day}, half_hour={todo.reminded_half_hour}")

                if (time_diff <= 30 * 60 and time_diff > 0 and todo.reminded_half_hour == 0):
                    reminder_todo = todo
                    reminder_type = "half_hour"
                    logger.info(f"[Reminder] Found HALF_HOUR reminder: todo {todo.id} ({todo.title}), {minutes_left:.1f}m left, DDL={todo.ddl}")
                    break

                if (24 * 3600 >= time_diff > 30 * 60 and todo.reminded_one_day == 0):
                    if reminder_todo is None:
                        reminder_todo = todo
                        reminder_type = "one_day"
                        logger.info(f"[Reminder] Found ONE_DAY reminder: todo {todo.id} ({todo.title}), {hours_left:.1f}h left, DDL={todo.ddl}")

            if reminder_todo and reminder_type:
                logger.info(f"[Reminder] Triggering {reminder_type} reminder for todo {reminder_todo.id}")
                self._trigger_reminder(reminder_todo, reminder_type)
                return True

            logger.debug("[Reminder] No todos need reminders")
            return False

        except Exception as e:
            logger.error(f"[Reminder] Error scanning reminders: {e}", exc_info=True)
            return False

    def _trigger_reminder(self, todo, reminder_type: str):
        """Trigger a reminder for a specific todo."""
        try:
            logger.info(f"Triggering {reminder_type} reminder for todo {todo.id}: {todo.title}")

            ai_response = self._generate_reminder_message(todo, reminder_type)

            self.todo_service.mark_reminder_sent(todo.id, reminder_type)

            if self.on_reminder_callback:
                self.on_reminder_callback({
                    "todo_id": todo.id,
                    "title": todo.title,
                    "emotion": ai_response.get("emotion", "default"),
                    "message": ai_response.get("reply", ""),
                    "reminder_type": reminder_type
                })

            logger.info(f"Reminder triggered successfully: todo {todo.id}")

        except Exception as e:
            logger.error(f"Error triggering reminder: {e}")

    def _generate_reminder_message(self, todo, reminder_type: str) -> Dict[str, Any]:
        """Generate personalized reminder message using AI or fallback."""
        try:
            ai_response = self._call_ai_for_reminder(todo, reminder_type)
            if ai_response:
                return ai_response
        except Exception as e:
            logger.warning(f"AI reminder generation failed: {e}")

        return self._generate_fallback_reminder(todo, reminder_type)

    def _call_ai_for_reminder(self, todo, reminder_type: str) -> Optional[Dict[str, Any]]:
        """Call AI to generate personalized reminder."""
        if not self.ai_client.is_available():
            logger.info(f"[ReminderAI] AI not available for todo_id={todo.id}, type={reminder_type}")
            return None

        try:
            logger.info(f"[ReminderAI] Calling AI for reminder: todo_id={todo.id}, type={reminder_type}")

            now = datetime.now()
            ddl_time = datetime.strptime(todo.ddl, "%Y-%m-%d %H:%M:%S")
            time_diff = ddl_time - now
            remaining_hours = time_diff.total_seconds() / 3600
            remaining_minutes = (time_diff.total_seconds() % 3600) / 60

            time_str = ""
            if remaining_hours >= 1:
                time_str = f"约 {int(remaining_hours)} 小时"
            else:
                time_str = f"约 {int(remaining_minutes)} 分钟"

            reminder_tone = "提前准备" if reminder_type == "one_day" else "紧急提醒"

            # Find matching category and example replies
            category, examples = self._find_category_and_examples(todo.title, todo.description or "", reminder_type)
            category_info = ""
            if category and examples:
                example_list = list(examples.values())[:2]  # Show first 2 examples
                example_text = "\n".join([f"- {ex}" for ex in example_list])
                category_info = f"\n【参考风格（{category}类）】\n{example_text}\n这里是示例，请根据下面的待办信息生成个性化回复，不要仅简单复制示例。"
                logger.info(f"[ReminderAI] Matched category: {category} for todo_id={todo.id}")
            else:
                logger.info(f"[ReminderAI] No category matched for todo_id={todo.id}, using generic prompt")

            # Get forbidden words constraint
            forbidden_constraint = get_forbidden_words_prompt()

            prompt = f"""你是用户的桌宠，正在发送待办事项提醒。提醒应该自然、有趣、体现桌宠个性！

【{todo.title}】
描述：{todo.description or "无"}
截止时间：{todo.ddl}
剩余时间：{time_str}
提醒类型：{reminder_tone}{category_info}

要求：
- 【重要】提醒中必须提及"【{todo.title}】"或具体事项名字
- 【重要】必须提及截止时间或剩余时间（不能忽略时间信息）
- 根据事项类型调整语气和情绪
- 50字以内为佳，最多不超过80汉字
- 自然、有趣、富有个性，不要太生硬{forbidden_constraint}

返回严格 JSON，不要任何前缀或后缀：
{{"emotion":"default|happy|annoyed|upset之一","reply":"提醒内容"}}"""

            response = self.ai_client.generate_reminder_reply(prompt)

            if response and "reply" in response and "emotion" in response:
                # Check if response contains forbidden words
                if contains_forbidden_word(response["reply"]):
                    logger.warning(f"[ReminderAI] AI response contains forbidden words for todo_id={todo.id}, using fallback")
                    return None

                logger.info(f"[ReminderAI] AI reminder generated successfully: todo_id={todo.id}, emotion={response['emotion']}")
                return response
            else:
                logger.warning(f"[ReminderAI] AI returned invalid response for todo_id={todo.id}")

        except Exception as e:
            logger.warning(f"[ReminderAI] Error calling AI for reminder: todo_id={todo.id}, error={e}")

        return None

    def _generate_fallback_reminder(self, todo, reminder_type: str) -> Dict[str, Any]:
        """Generate fallback reminder using local rules with specific title and DDL."""
        logger.info(f"[ReminderAI] Using fallback reminder: todo_id={todo.id}, type={reminder_type}")

        title = (todo.title or "").lower()
        description = (todo.description or "").lower()
        content = f"{title} {description}"

        # Calculate remaining time
        try:
            now = datetime.now()
            ddl_time = datetime.strptime(todo.ddl, "%Y-%m-%d %H:%M:%S")
            time_diff = ddl_time - now
            hours = int(time_diff.total_seconds() // 3600)
            minutes = int((time_diff.total_seconds() % 3600) // 60)

            if hours > 0:
                remaining = f"还有{hours}小时{minutes}分"
            else:
                remaining = f"还有{minutes}分"
        except:
            remaining = ""

        display_ddl = f"截止{todo.ddl}" if todo.ddl else ""

        if any(keyword in content for keyword in ["考试", "exam", "test"]):
            emotion = "happy"
            if reminder_type == "one_day":
                reply = f"【{todo.title}】{display_ddl}。记得复习重点，祝考试顺利！"
            else:
                reply = f"【{todo.title}】{remaining}（{display_ddl}）。放松心态，加油！"

        elif any(keyword in content for keyword in ["作业", "homework", "assignment"]):
            emotion = "annoyed"
            if reminder_type == "one_day":
                reply = f"【{todo.title}】{display_ddl}，别又拖到最后才交。"
            else:
                reply = f"【{todo.title}】{remaining}截止！赶紧交上去！"

        elif any(keyword in content for keyword in ["组会", "meeting", "会议"]):
            emotion = "default"
            if reminder_type == "one_day":
                reply = f"【{todo.title}】{display_ddl}。材料准备好，别迟到。"
            else:
                reply = f"【{todo.title}】{remaining}（{display_ddl}）。赶紧出门！"

        elif any(keyword in content for keyword in ["出去玩", "旅行", "travel", "trip"]):
            emotion = "happy"
            if reminder_type == "one_day":
                reply = f"【{todo.title}】快到啦！{display_ddl}，记得看天气、带伞。"
            else:
                reply = f"【{todo.title}】{remaining}该出发了！带好东西，玩得开心！"

        elif any(keyword in content for keyword in ["面试", "interview"]):
            emotion = "default"
            if reminder_type == "one_day":
                reply = f"【{todo.title}】{display_ddl}。检查材料，放松心态早出门。"
            else:
                reply = f"【{todo.title}】{remaining}（{display_ddl}）。深呼吸，准备好！"

        elif any(keyword in content for keyword in ["论文", "paper"]):
            emotion = "annoyed"
            if reminder_type == "one_day":
                reply = f"【{todo.title}】{display_ddl}。保存文档、检查格式，别乱来。"
            else:
                reply = f"【{todo.title}】{remaining}截止！最后冲刺！"

        else:
            emotion = "default"
            if reminder_type == "one_day":
                reply = f"【{todo.title}】{display_ddl}。记得提前处理一下。"
            else:
                reply = f"【{todo.title}】{remaining}({display_ddl})。赶紧处理！"

        # Truncate to 60 chars max
        if len(reply) > 60:
            reply = reply[:57] + "..."

        return {"emotion": emotion, "reply": reply}
