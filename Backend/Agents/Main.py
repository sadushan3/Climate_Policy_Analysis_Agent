from fastapi import FastAPI
from Backend.Agents.IT22180520_Sadushan_Agent.Routes import comparator_routes
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv