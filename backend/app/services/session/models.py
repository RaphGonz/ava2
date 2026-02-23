from enum import Enum


class ConversationMode(str, Enum):
    SECRETARY = "secretary"
    INTIMATE = "intimate"


Message = dict  # {"role": "user"|"assistant", "content": str}
