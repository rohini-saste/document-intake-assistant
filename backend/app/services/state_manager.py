from app.models.schema import IntakeState, ExtractionResult

class StateManager:
    """
    Manages the logic of accumulating state and deciding next steps.
    """
    def merge_state(self, current: IntakeState, extraction: ExtractionResult) -> IntakeState:
        """
        Merges new extraction results into the current state.
        If extraction contains a non-null value, it overwrites the current state.
        """
        new_state = current.model_copy(deep=True)
        
        if extraction.full_name is not None:
            new_state.full_name = extraction.full_name
        if extraction.home_address is not None:
            new_state.home_address = extraction.home_address
        if extraction.covers_worldwide_assets is not None:
            new_state.covers_worldwide_assets = extraction.covers_worldwide_assets
        if extraction.has_children is not None:
            new_state.has_children = extraction.has_children
        if extraction.children_names is not None:
            new_state.children_names = extraction.children_names
            
        if extraction.executor_name is not None:
            new_state.executor.name = extraction.executor_name
        if extraction.executor_relationship is not None:
            new_state.executor.relationship = extraction.executor_relationship
            
        if extraction.backup_executor_name is not None:
            new_state.backup_executor.name = extraction.backup_executor_name
        if extraction.backup_executor_relationship is not None:
            new_state.backup_executor.relationship = extraction.backup_executor_relationship
            
        if extraction.specific_gifts is not None:
            new_state.specific_gifts = extraction.specific_gifts
        if extraction.additional_wishes is not None:
            new_state.additional_wishes = extraction.additional_wishes
            
        return new_state

    def get_next_question(self, state: IntakeState) -> str:
        """
        Determines the next logical question to ask based on missing state.
        """
        if state.full_name is None:
            return "Could you please provide your full name?"
        if state.home_address is None:
            return "What is your home address?"
        if state.covers_worldwide_assets is None:
            return "Does this document need to cover worldwide assets, or just domestic?"
        if state.has_children is None:
            return "Do you have any children?"
        if state.has_children is True and state.children_names is None:
            return "What are the names of your children?"
        if state.executor.name is None:
            return "Who would you like to appoint as your executor?"
        if state.executor.relationship is None:
            return "What is your relationship to your executor?"
        if state.backup_executor.name is None:
            return "Who would you like to appoint as your secondary or backup executor? (You can say 'None' if you don't want one)"
        if state.backup_executor.relationship is None and state.backup_executor.name.lower() != "none":
            return "What is your relationship to your backup executor?"
        if state.specific_gifts is None:
            return "Are there any specific gifts you would like to leave to anyone?"
        if state.additional_wishes is None:
            return "Do you have any additional wishes to include?"
            
        return "Thank you. It looks like we have gathered all the necessary information. Is there anything you would like to change?"
