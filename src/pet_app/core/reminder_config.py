"""Configurable reminder templates and keyword mappings."""

# Reminder config for different types of todos
REMINDER_KEYWORDS = {
    "exam": {
        "keywords": ["考试", "exam", "test", "期末", "期中", "考"],
        "one_day": {
            "happy": "【{title}】快到啦！截止 {ddl}，记得复习重点，祝你会的都对。",
            "annoyed": "【{title}】快来温习一下，截止 {ddl}，别临时抱佛脚。"
        },
        "half_hour": {
            "happy": "【{title}】时间要到了！{ddl} 开始，放松心态，祝顺利～",
            "annoyed": "【{title}】已经{remaining}后开始啦！赶紧深呼吸准备好！"
        }
    },
    "homework": {
        "keywords": ["作业", "homework", "assignment", "练习"],
        "one_day": {
            "annoyed": "【{title}】快到截止啦，{ddl} 前要交！别又拖到最后。",
            "default": "【{title}】截止时间是 {ddl}，抓紧时间做起来吧。"
        },
        "half_hour": {
            "annoyed": "【{title}】真的快到期了！{ddl} 就关闭了，赶紧交！",
            "default": "【{title}】只剩 {remaining} 了，冲刺交作业！"
        }
    },
    "meeting": {
        "keywords": ["组会", "meeting", "会议", "讨论", "standup"],
        "one_day": {
            "default": "【{title}】明天左右要开始了，材料检查好，时间记清楚。",
            "happy": "【{title}】准备一下资料吧，{ddl} 还要开会呢。"
        },
        "half_hour": {
            "default": "【{title}】会议时间快到了！{ddl} 开始，抓紧出门别迟到！",
            "annoyed": "【{title}】只有 {remaining} 了！赶紧出门，别迟到！"
        }
    },
    "travel": {
        "keywords": ["出去玩", "旅行", "travel", "trip", "游玩", "度假", "玩"],
        "one_day": {
            "happy": "【{title}】快到了！{ddl} 出发，记得看天气、带伞，玩得开心～",
            "default": "【{title}】明天左右要出发了，检查一下行李清单。"
        },
        "half_hour": {
            "happy": "【{title}】该出发啦！现在 {remaining} 后，记得带好东西！",
            "default": "【{title}】真的要出门了，{remaining} 后可不能再找东西了！"
        }
    },
    "interview": {
        "keywords": ["面试", "interview", "校招", "社招", "笔试"],
        "one_day": {
            "default": "【{title}】{ddl} 要面试啦，检查一下准备工作，放松心态。",
            "happy": "【{title}】机会来啦！{ddl} 面试，好好表现自己！"
        },
        "half_hour": {
            "default": "【{title}】面试时间快到了！{ddl} 开始，深呼吸，准备好！",
            "annoyed": "【{title}】只有 {remaining} 了，赶紧出门别迟到！"
        }
    },
    "paper": {
        "keywords": ["论文", "paper", "报告", "文章", "初稿"],
        "one_day": {
            "annoyed": "【{title}】截止 {ddl}，保存好文档、检查格式，别乱来。",
            "default": "【{title}】快到截止了，{ddl} 前要完成的。"
        },
        "half_hour": {
            "annoyed": "【{title}】真的快过期了！{ddl} 就截止，最后冲刺！",
            "default": "【{title}】只有 {remaining} 了，抓紧检查内容、提交！"
        }
    },
    "food": {
        "keywords": ["吃", "餐厅"],
        "one_day": {
            "happy": "别忘了 {ddl}的【{title}】，听起来很好吃。",
            "default": "{ddl}要去【{title}】，别忘了提前预约哦。"
        },
        "half_hour": {
            "happy": "【{title}】只有 {remaining} 了，该出门啦。",
            "default": "【{title}】只有 {remaining} 了，赶紧出门！"
        }
    },
    "deadline": {
        "keywords": ["截止", "ddl", "deadline", "提交", "完成"],
        "one_day": {
            "default": "【{title}】{ddl} 前要完成，准备一下吧。"
        },
        "half_hour": {
            "default": "【{title}】时间快到了！{remaining} 后截止，抓紧完成！"
        }
    }
}

# Default reminder template (used for unknown types)
DEFAULT_REMINDER = {
    "one_day": {
        "default": "【{title}】快到截止时间了。截止 {ddl}，提前准备一下。"
    },
    "half_hour": {
        "default": "【{title}】时间要到了！{remaining} 后截止，赶紧处理！"
    }
}


def find_reminder_template(title: str, description: str, reminder_type: str) -> dict:
    """Find matching reminder template based on keywords."""
    content = f"{title} {description}".lower()

    for category, config in REMINDER_KEYWORDS.items():
        keywords = config.get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in content:
                return config.get(reminder_type, {})

    # Return default if no keyword matched
    return DEFAULT_REMINDER.get(reminder_type, {})


def render_reminder_template(template: str, title: str, ddl: str, remaining: str) -> str:
    """Render reminder template with variables."""
    return template.format(
        title=title,
        ddl=ddl,
        remaining=remaining
    )


# Forbidden words in reminder messages
# AI will be instructed NOT to use these words at the start or in response
REMINDER_FORBIDDEN_WORDS = [
    # Add words/phrases that AI should avoid, one per line
    # Example: "喂", "喂喂喂", "嗯", "哎呀"
    "喂",
    "喂喂喂",
    "呐",
    "哎哟",
    "哎呀",
    "哎",
    "喵"
]


def get_forbidden_words_prompt() -> str:
    """Generate forbidden words constraint for AI prompt."""
    if not REMINDER_FORBIDDEN_WORDS:
        return ""

    forbidden_list = "、".join(REMINDER_FORBIDDEN_WORDS)
    return f"\n- 不要以这些词开头或频繁使用：{forbidden_list}"


def contains_forbidden_word(text: str) -> bool:
    """Check if generated text contains forbidden words."""
    text_lower = text.lower()
    for word in REMINDER_FORBIDDEN_WORDS:
        if word.lower() in text_lower:
            return True
    return False
