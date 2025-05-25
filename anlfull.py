import telebot
from telebot import util
from gigachat_api import analyze_prompt_with_gigachat, query_gigachat_for_feedback
from wikipedia_api import get_wikipedia_summary, get_wikipedia_article_for_llama
from data_handler import load_data, save_data, register_user, update_progress, update_test_results, load_tests, THEMES, get_additional_materials_for_topic_with_llama, get_user_stats, get_test_for_theme, search_medium, search_arxiv, update_experince
from utils import get_next_theme, extract_topic_from_prompt, cache_prompt_analysis, get_cached_analysis
from keyboard import create_test_keyboard
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import re
import os
import json
from dotenv import load_dotenv
from bot import bot
import requests
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from main import evaluate_prompt
CACHE_DIR = "cache"

def analyze_prompt_full(user_prompt: str):
    topic = extract_topic_from_prompt(user_prompt)
    if not topic:
        return {"error": "Тема не определена"}

    enriched_prompt = f"Промпт пользователя:\n{user_prompt}"

    ollama_feedback = analyze_prompt_with_gigachat(enriched_prompt)
    prompt_evaluation = evaluate_prompt(user_prompt)

    return {
        "prompt": user_prompt,
        "topic": topic,
        "llm_feedback": ollama_feedback,
        "evaluation": prompt_evaluation
    }