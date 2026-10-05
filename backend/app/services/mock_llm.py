import re
from typing import Tuple, List, Optional
from app.models.schema import IntakeState, ExtractionResult
from app.services.llm_provider import LLMProvider

class MockLLMProvider(LLMProvider):
    """
    Deterministic smart mock LLM.
    Extracts entities based on regular expressions, semantic heuristics, and conversational context.
    Uses strict word boundaries to avoid false substring matches.
    """
    def extract_and_respond(self, user_message: str, current_state: IntakeState) -> Tuple[ExtractionResult, str]:
        raw_msg = user_message.strip()
        msg = raw_msg.lower()
        result = ExtractionResult()
        
        # -------------------------------------------------------------
        # 1. Full Name Extraction & Corrections
        # -------------------------------------------------------------
        name_match = re.search(
            r'(?:my name is|i am|call me|name is|name to|name:)\s+([a-zA-Z\s\.\'-]+?)(?:,|\.|\band\b|\bmy\b|$)', 
            raw_msg, 
            re.IGNORECASE
        )
        if name_match:
            candidate = name_match.group(1).strip()
            if candidate and len(candidate.split()) <= 4:
                result.full_name = candidate.title()
        elif current_state.full_name is None:
            # First turn direct input (e.g. "Rohini Saste" or "Jane Doe")
            words = raw_msg.split()
            is_non_name = bool(re.search(r'\b(hello|hi|hey|help|yes|no|maybe|later|idk|not sure|skip|pass|wait|why|what|how|sorry|thanks|thank you|something)\b', msg))
            if 1 <= len(words) <= 4 and not is_non_name and all(w.isalpha() for w in words):
                result.full_name = raw_msg.title()

        # -------------------------------------------------------------
        # 2. Home Address Extraction & Corrections
        # -------------------------------------------------------------
        address_match = re.search(
            r'(?:live at|living at|address is|address to|address:)\s+(.*?)(?:;|\.|\b(?:worldwide|domestic|children|kids|executor|gifts?|wishes?|no children|no kids)\b|$)', 
            raw_msg, 
            re.IGNORECASE
        )
        if address_match:
            result.home_address = address_match.group(1).strip().rstrip(',').strip()
        elif current_state.home_address is None and (current_state.full_name is not None or result.full_name is not None) and result.full_name != raw_msg.title():
            # Sequential answering to address question (e.g. "pune", "London", "123 Main Street")
            is_non_address = bool(re.search(r'^\s*(hello|hi|hey|help|why|what|how|skip|pass|idk|not sure)\s*$', msg))
            if not is_non_address and len(raw_msg) > 1:
                result.home_address = raw_msg.strip().title() if len(raw_msg.split()) <= 2 else raw_msg.strip()

        # -------------------------------------------------------------
        # 3. Estate Scope (Worldwide vs Domestic)
        # -------------------------------------------------------------
        if re.search(r'\b(worldwide|global|international|everywhere|all countries)\b', msg):
            result.covers_worldwide_assets = True
        elif re.search(r'\b(domestic|local|only domestic|domestic only|just domestic|uk only|us only|india only)\b', msg):
            result.covers_worldwide_assets = False
        elif current_state.covers_worldwide_assets is None and (current_state.home_address is not None or result.home_address is not None):
            if re.search(r'\b(yes|y|yeah|yep|worldwide)\b', msg):
                result.covers_worldwide_assets = True
            elif re.search(r'\b(no|n|nope|domestic|just domestic|domestic only)\b', msg):
                result.covers_worldwide_assets = False

        # -------------------------------------------------------------
        # 4. Children & Children Names
        # -------------------------------------------------------------
        # Check combined statement e.g. "I have 2 kids: Alice and Bob" or "Children: Alice, Bob"
        kids_names_match = re.search(r'(?:children(?:\s+are|\s*:)?|kids(?:\s+are|\s*:)?|children named)\s+([a-zA-Z,\s&]+)', raw_msg, re.IGNORECASE)
        if kids_names_match and not re.search(r'\b(no children|no kids|don\'t have|none)\b', msg):
            parsed_names = [n.strip().title() for n in re.split(r'[,&]|\band\b', kids_names_match.group(1)) if n.strip()]
            if parsed_names:
                result.has_children = True
                result.children_names = parsed_names

        if result.has_children is None:
            if re.search(r'\b(no children|no kids|don\'t have children|don\'t have any kids|have no children)\b', msg):
                result.has_children = False
                result.children_names = []
            elif re.search(r'\b(i have children|i have kids|have a son|have a daughter|have children|have kids)\b', msg):
                result.has_children = True
            elif current_state.has_children is None and current_state.covers_worldwide_assets is not None:
                if re.search(r'^\s*(no|nope|none|n)\s*$', msg):
                    result.has_children = False
                    result.children_names = []
                elif re.search(r'^\s*(yes|yep|yeah|y|i do)\s*$', msg):
                    result.has_children = True

        # If has_children is True and we're expecting children names
        if (current_state.has_children is True or result.has_children is True) and current_state.children_names is None and result.children_names is None:
            if not re.search(r'^\s*(yes|y|i do|no|none)\s*$', msg):
                names = [n.strip().title() for n in re.split(r'[,&]|\band\b', raw_msg) if n.strip()]
                if names:
                    result.children_names = names

        # -------------------------------------------------------------
        # 5. Executor Details (Name & Relationship)
        # -------------------------------------------------------------
        # Combined pattern: "My brother James is my executor" or "Sarah (sister)" or "Sarah, my sister"
        combined_exec1 = re.search(r'my\s+(brother|sister|friend|wife|husband|spouse|son|daughter|partner|solicitor|lawyer|father|mother)\s+([a-zA-Z\s]+?)(?:\s+is\s+my\s+executor|\s+as\s+executor|\.|$)', raw_msg, re.IGNORECASE)
        combined_exec2 = re.search(r'(?:executor(?:\s+is|\s*:)?\s+)?([a-zA-Z\s]+?)\s*[\(\,]\s*(?:my\s+)?(brother|sister|friend|wife|husband|spouse|son|daughter|partner|solicitor|lawyer|father|mother)\s*[\)]?', raw_msg, re.IGNORECASE)
        combined_exec3 = re.search(r'(?:appoint|executor is)\s+([a-zA-Z\s]+?)\s+who is my\s+(brother|sister|friend|wife|husband|spouse|son|daughter|partner|solicitor|lawyer)', raw_msg, re.IGNORECASE)
        
        if combined_exec1:
            result.executor_relationship = combined_exec1.group(1).title()
            result.executor_name = combined_exec1.group(2).strip().title()
        elif combined_exec2:
            result.executor_name = combined_exec2.group(1).strip().title()
            result.executor_relationship = combined_exec2.group(2).title()
        elif combined_exec3:
            result.executor_name = combined_exec3.group(1).strip().title()
            result.executor_relationship = combined_exec3.group(2).title()
        else:
            # Standalone Executor Name
            exec_name_match = re.search(r'(?:executor is|appoint|executor:)\s+([a-zA-Z\s\.\'-]+?)(?:,|\.|$)', raw_msg, re.IGNORECASE)
            if exec_name_match:
                result.executor_name = exec_name_match.group(1).strip().title()
            elif (current_state.children_names is not None or current_state.has_children is False):
                if current_state.executor.name is None and len(raw_msg.split()) <= 4 and not re.search(r'^\s*(no|none)\s*$', msg):
                    result.executor_name = raw_msg.title()

            # Standalone Executor Relationship
            if (current_state.executor.name is not None or result.executor_name is not None) and current_state.executor.relationship is None:
                rel_match = re.search(r'\b(brother|sister|friend|wife|husband|spouse|son|daughter|partner|solicitor|lawyer|father|mother|colleague|cousin)\b', msg)
                if rel_match:
                    result.executor_relationship = rel_match.group(1).title()
                elif len(raw_msg.split()) <= 3 and result.executor_name is None:
                    result.executor_relationship = raw_msg.title()

        # -------------------------------------------------------------
        # 5.5 Backup Executor Details
        # -------------------------------------------------------------
        if current_state.executor.relationship is not None:
            if current_state.backup_executor.name is None and result.backup_executor_name is None and result.specific_gifts is None:
                if len(raw_msg.split()) <= 4 and re.search(r'^\s*(no|none)\s*$', msg):
                    result.backup_executor_name = "None"
                elif len(raw_msg.split()) <= 4:
                    result.backup_executor_name = raw_msg.title()
            elif current_state.backup_executor.name is not None and current_state.backup_executor.name.lower() != "none" and current_state.backup_executor.relationship is None and result.backup_executor_relationship is None:
                rel_match = re.search(r'\b(brother|sister|friend|wife|husband|spouse|son|daughter|partner|solicitor|lawyer|father|mother|colleague|cousin)\b', msg)
                if rel_match:
                    result.backup_executor_relationship = rel_match.group(1).title()
                elif len(raw_msg.split()) <= 3:
                    result.backup_executor_relationship = raw_msg.title()

        # -------------------------------------------------------------
        # 6. Specific Gifts Extraction & Corrections
        # -------------------------------------------------------------
        gift_explicit = re.search(r'(?:specific gifts?|gifts?|leave)\s*:\s*(.*)', raw_msg, re.IGNORECASE)
        if gift_explicit:
            result.specific_gifts = gift_explicit.group(1).strip()
        elif current_state.executor.relationship is not None and (current_state.backup_executor.name == "None" or current_state.backup_executor.relationship is not None) and current_state.specific_gifts is None and result.backup_executor_name is None and result.backup_executor_relationship is None:
            if re.search(r'\b(no|none|nothing|no gifts|no specific gifts|n/a|none specified)\b', msg):
                result.specific_gifts = "None"
            else:
                result.specific_gifts = raw_msg

        # -------------------------------------------------------------
        # 7. Additional Wishes Extraction & Corrections
        # -------------------------------------------------------------
        wishes_explicit = re.search(r'(?:additional wishes?|wishes?)\s*:\s*(.*)', raw_msg, re.IGNORECASE)
        if wishes_explicit:
            result.additional_wishes = wishes_explicit.group(1).strip()
        elif current_state.specific_gifts is not None and current_state.additional_wishes is None:
            if re.search(r'\b(no|none|nothing|no additional wishes|no wishes|n/a|none specified)\b', msg):
                result.additional_wishes = "None"
            else:
                result.additional_wishes = raw_msg

        return result, ""

