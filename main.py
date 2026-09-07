from gerador_matches import get_matches
from pathlib import Path
from connection import connect_to_database

DIR_PROJETO = Path(__file__).resolve().parent

df = get_matches()

