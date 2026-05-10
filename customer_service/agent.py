"""Agent module for the customer service agent - Lazizah Aqiqah."""
import logging
import warnings

from google.adk import Agent
from google.adk.apps import App

from .config import Config
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION
from .shared_libraries.callbacks import (
    after_tool,
    before_agent,
    before_tool,
    rate_limit_callback,
)
from .tools.tools import (
    cek_stok_kambing,
    cek_paket_layanan,
    cek_setting,
    cek_jadwal,
    cek_faq,
    catat_prospek,
    get_tanggal_hari_ini, simpan_prospek,
)

warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

configs = Config()
logger = logging.getLogger(__name__)

root_agent = Agent(
    model=configs.agent_settings.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=INSTRUCTION,
    name="Delisa",
    tools=[
        cek_stok_kambing,
        cek_paket_layanan,
        cek_setting,
        cek_jadwal,
        cek_faq,
        catat_prospek,
        get_tanggal_hari_ini, simpan_prospek,
    ],
    before_tool_callback=before_tool,
    after_tool_callback=after_tool,
    before_agent_callback=before_agent,
    before_model_callback=rate_limit_callback,
)

app = App(root_agent=root_agent, name="customer_service")
