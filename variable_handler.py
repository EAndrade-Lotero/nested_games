from psynet.utils import get_logger

logger = get_logger()


class VariableHandler:

    possible_levels = ["top", "trial", "answer"]
    debug = True

    def __init__(self, level: str = "top", use_vars: bool = False) -> None:
        assert level in self.possible_levels, f"Error: level should be one of {self.possible_levels} but got {level}."
        self.level = level
        self.use_vars = use_vars

    def set_value(self, participant, variable, value) -> None:
        _ = self.get_value(participant, variable)
        data = self.get_data_at_level(participant)
        if self.use_vars:
            data[variable] = value
        else:
            setattr(data, variable, value)

    def get_value(self, participant, variable: str):
        if self.use_vars:
            return self.get_from_vars(participant, variable)
        else:
            return self.get_from_var(participant, variable)

    def set_dictionary_value(self, participant, dictionary_name, key, value):
        dictionary = self.get_value(participant, dictionary_name)
        if self.debug:
            logger.info(f"VariableHandler is using dictionary: {dictionary_name}")
            logger.info(f"{dictionary}")
        dictionary[key] = value
        if self.debug:
            logger.info("Value added =>>")
            logger.info(f"{dictionary}")

    def get_dictionary_value(self, participant, dictionary_name, key):
        dictionary = self.get_value(participant, dictionary_name)
        if self.debug:
            logger.info(f"VariableHandler is using dictionary: {dictionary_name}")
            logger.info(f"{dictionary}")
        value = dictionary[key]
        if self.debug:
            logger.info(f"Value retrieved =>> {value}")
        return value

    def get_from_var(self, participant, variable: str):
        data = self.get_data_at_level(participant)
        if data.has(variable):
            return getattr(participant.var, variable)
        else:
            return None

    def get_from_vars(self, participant, variable):
        data = self.get_data_at_level(participant)
        try:
            value = data[variable]
            if self.debug:
                logger.info(f"VariableHandler succeeded ==> {variable} has value {value} (type: {type(value)})")
            return value
        except ValueError:
            data[variable] = None
            if self.debug:
                logger.info(f"VariableHandler error ==> {variable} doesn't exist in vars at level {self.level}")
            return None

    def get_data_at_level(self, participant):
        if self.use_vars:
            if self.level == "top":
                data = participant.vars
            elif self.level == "trial":
                error_msg = "Variable handler error: participant doesn't have current_trial.\n"
                error_msg += f"Attribute of participant's: \n{vars(participant)}"
                assert hasattr(participant, "current_trial"), error_msg
                data = participant.current_trial.vars
            else:
                raise NotImplementedError(f"Error: Level {self.level} not implemented!")
        else:
            # Here is var and not vars <= note the final 's'
            if self.level == "top":
                data = participant.var
            elif self.level == "answer":
                error_msg = "Variable handler error: participant doesn't have current_trial.\n"
                error_msg += f"Attribute of participant's: \n{vars(participant)}"
                assert hasattr(participant, "current_trial"), error_msg
                data = participant.current_trial.var
            else:
                raise NotImplementedError(f"Error: Level {self.level} not implemented!")
        return data

    @staticmethod
    def get_value_from_last_answer(participant, page_label: str):
        last_answer = participant.answer_accumulators[-1]
        assert isinstance(last_answer, dict)
        value = VariableHandler.get_from_answer(
            answer=last_answer,
            variable=page_label,
        )
        return value

    @staticmethod
    def set_value_from_last_answer(participant, page_label: str, variable: str):
        value = VariableHandler.get_value_from_last_answer(participant, page_label)
        participant.current_trial.vars[variable] = value

    @staticmethod
    def get_from_answer(answer, variable):

        if answer is None:
            return None

        initial_values = [
            value for key, value in answer.items()
            if key.startswith(variable)
        ]
        values = [
            value for value in initial_values
            if (
                value is not None
                and str(value) != "null"
                and value != 'INVALID_RESPONSE'
            )
        ]
        err_msg = f"Error while finding a value for {variable}\n"
        err_msg += f"The observed trial answer was {answer}\n"
        err_msg += f"The initial values observed were {initial_values}\n"
        err_msg += f"The non-empty values found were {values}"
        assert len(values) == 1, err_msg
        return values[0]


# InfoPage(
#     content=f"""
# My id: {self.participant_id} ---
# My outer role: {self.get_outer_role(self.participant)} ---
# Am I the outer leader?: {self.is_the_outer_leader(self.participant)} ---
# Participant to be the inner PROPOSER: {self.get_outer_result()} ---
# Continue to inner game?: {self.continue_to_inner_game()} ---
# Answer: {self.participant.answer} ---
# Answer accumulators: {self.participant.answer_accumulators} ---
# """,
#     time_estimate=5,
# ),

# InfoPage(
#     content=f"""
# My id: {self.participant_id} ---
# My inner role: {self.get_inner_role(self.participant)} ---
# Am I the inner leader?: {self.is_the_inner_leader(self.participant)} ---
# Proposal: {variable_handler.get_value(participant, "inner_proposal")} ---
# Result: {self.get_inner_result()} ---
# Answer: {self.participant.answer} ---
# Answer accumulators: {self.participant.answer_accumulators} ---
# """,
#     time_estimate=5,
# ),
