from environs import Env

env = Env()
env.read_env()

API_TOKEN = env.str("API_TOKEN")

INITIATIVE_ID = env.str("INITIATIVE_ID")
