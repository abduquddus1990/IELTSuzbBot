"""Finite State Machine (FSM) States for IELTS & Uzbekistan CEFR Mock Exam Sessions."""

from aiogram.fsm.state import State, StatesGroup


class ExamSessionStates(StatesGroup):
    """Step-by-step FSM states for conducting a 4-skill IELTS or CEFR mock exam in Telegram."""

    choosing_exam_type = State()
    choosing_exam_mode = State()
    taking_listening_reading = State()
    submitting_writing_task_1 = State()
    submitting_writing_task_2 = State()
    submitting_speaking_part_1 = State()
    submitting_speaking_part_2 = State()
    submitting_speaking_part_3 = State()


__all__ = ["ExamSessionStates"]
