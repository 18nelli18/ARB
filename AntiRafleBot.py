import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)


# États de la conversation
(
    START,
    LOCATION_TYPE,
    TRANSPORT_TYPE,
    TRAIN_STATION,
    METRO_STATION,
    BUS_STOP,
    LOCATION_DETAIL,
    OTHER_LOCATION,
    TIME_DELTA,
    TYPE_AGENT,
    POLICE_TYPE,
    AGENT_OTHER_TEXT,
    AGENT_COUNT,
    OTHER_AGENT_YN,
    INTERVENTION_TYPE,
    CONTROL_TYPE,
    AGGRESSION_DETAIL,
    TARGET_COUNT,
    ISSUE,
    TRANSMISSION,
    WITNESS_YN,
    WITNESS_SOURCE,
    CONTACT_YN
) = range(23)

# Claviers sans l'option 'Retour'
keyboard_start = [['Start']]

keyboard_location = [
    ['🚇 Transports'],
    ['🛣 Rue'],
    ['🔍 Autre']
]

keyboard_transport = [
    ['🚆 Train'],
    ['🚇 Metro RER'],
    ['🚍 Bus Tram']
]

keyboard_time = [
    ["⏰ À l'instant"],
    ['⏱ - de 15'],
    ['🕒 + de 15 min'],
    ['🕟 + de 30 min'],
    ['🕖 + de 45 min'],
    ['🕗 + de 1h']
]

keyboard_agent = [
    ['👮‍♂️ RATP Sureté'],
    ['🚔 Police'],
    ['👮‍♀️ Gendarmerie'],
    ['🕵️ Agent en civil'],
    ['⚠️ Extrême droite'],
    ['🆕 Autre']
]

keyboard_police = [
    ['🛂 Police aux frontières'],
    ['🚨 Police nationale'],
    ['🏛 Police municipale'],
    ['👮 Police en civil'],
    ['❓ Ne sais pas']
]

keyboard_yes_no = [
    ['✅ Oui'],
    ['❌ Non']
]

keyboard_intervention = [
    ['👀 Simple présence'],
    ['🛑 Contrôle'],
    ['⚔️ Agression']
]

keyboard_control = [
    ["🆔 Contrôle d'identité"],
    ['🎒 Fouille sac'],
    ['🩺 Fouille corps']
]

keyboard_issue = [
    ['🚨 Interpelé⸱e'],
    ['✅ Relâché⸱e'],
    ['⏳ Je n’ai pas (eu) le temps de rester']
]

# Fonction pour sauvegarder les rapports

def save_report(data, filename='report.json'):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reports = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        reports = []
    entry = {'timestamp': datetime.now().isoformat(), **data}
    reports.append(entry)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)

# Utilitaires de suppression
async def log_and_delete(message, context):
    context.user_data.setdefault('to_delete', []).append((message.chat_id, message.message_id))

async def delete_all(context):
    for chat_id, msg_id in context.user_data.get('to_delete', []):
        try:
            await context.bot.delete_message(chat_id, msg_id)
        except:
            pass
    context.user_data.clear()

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['start_time'] = datetime.now().isoformat()
    await log_and_delete(update.message, context)
    sent = await update.message.reply_text(
        "Bonjour, ceci est un formulaire automatique de signalement pour lutter contre les rafles."
        "\nCette discussion sera supprimée une fois terminée pour plus de sûreté."
        "\nPour commencer, veuillez cliquer sur Start.",
        reply_markup=ReplyKeyboardMarkup(keyboard_start, one_time_keyboard=True)
    )
    await log_and_delete(sent, context)
    return START

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    sent = await update.message.reply_text(
        "Où a (eu) lieu l'incident?",
        reply_markup=ReplyKeyboardMarkup(keyboard_location, one_time_keyboard=True)
    )
    await log_and_delete(sent, context)
    return LOCATION_TYPE

async def location_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    choice = update.message.text
    context.user_data['location_type'] = choice
    if choice == 'Transports':
        sent = await update.message.reply_text(
            "Quel type de transport?",
            reply_markup=ReplyKeyboardMarkup(keyboard_transport, one_time_keyboard=True)
        )
        await log_and_delete(sent, context)
        return TRANSPORT_TYPE
    else:
        sent = await update.message.reply_text(
            "Adresse ou nom du lieu (Veuillez préciser au max)",
            reply_markup=ReplyKeyboardMarkup([], one_time_keyboard=True)
        )
        await log_and_delete(sent, context)
        return OTHER_LOCATION

async def transport_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    t = update.message.text
    context.user_data['transport_type'] = t
    if t == 'Train':
        prompt, next_state = "Quelle gare?", TRAIN_STATION
    elif t == 'Metro RER':
        prompt, next_state = "Quelle station?", METRO_STATION
    else:
        prompt, next_state = "Quel arrêt?", BUS_STOP
    sent = await update.message.reply_text(prompt)
    await log_and_delete(sent, context)
    return next_state

async def train_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['train_station'] = update.message.text
    sent = await update.message.reply_text("Précisez au maximum la localisation (Ligne, destination, couloir, hall, entrée)")
    await log_and_delete(sent, context)
    return LOCATION_DETAIL

async def metro_station(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['metro_station'] = update.message.text
    sent = await update.message.reply_text("Précisez au maximum la localisation (Ligne, destination, couloir, hall, sortie)")
    await log_and_delete(sent, context)
    return LOCATION_DETAIL

async def bus_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['bus_stop'] = update.message.text
    sent = await update.message.reply_text("Précisez au maximum la localisation (Ligne, destination, couloir, hall, sortie)")
    await log_and_delete(sent, context)
    return LOCATION_DETAIL

async def location_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['location_detail'] = update.message.text
    sent = await update.message.reply_text(
        "Quand?",
        reply_markup=ReplyKeyboardMarkup(keyboard_time, one_time_keyboard=True)
    )
    await log_and_delete(sent, context)
    return TIME_DELTA

async def other_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['other_location'] = update.message.text
    sent = await update.message.reply_text(
        "Quand?",
        reply_markup=ReplyKeyboardMarkup(keyboard_time, one_time_keyboard=True)
    )
    await log_and_delete(sent, context)
    return TIME_DELTA

async def time_delta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['time_delta'] = update.message.text
    sent = await update.message.reply_text(
        "Quel type d'agent?",
        reply_markup=ReplyKeyboardMarkup(keyboard_agent, one_time_keyboard=True)
    )
    await log_and_delete(sent, context)
    return TYPE_AGENT

async def type_agent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    agent = update.message.text
    context.user_data.setdefault('agents', []).append({'type': agent})
    if agent == '🚔 Police':
        media = [
           InputMediaPhoto(open('./paf.png',   'rb')),
           InputMediaPhoto(open('./national.png',  'rb')),
           InputMediaPhoto(open('./police.png','rb'))
        ]
        sent_photos = await context.bot.send_media_group(
           chat_id=update.effective_chat.id,
           media=media
        )
        for msg in sent_photos:
           await log_and_delete(msg, context)
        
        sent = await update.message.reply_text(
            "Quelle police?",
            reply_markup=ReplyKeyboardMarkup(keyboard_police, one_time_keyboard=True)
        )
        await log_and_delete(sent, context)
        return POLICE_TYPE
    elif agent == 'Autre':
        sent = await update.message.reply_text("Précisez? ")
        await log_and_delete(sent, context)
        return AGENT_OTHER_TEXT
    else:
        sent = await update.message.reply_text("Nombre d'agents? ")
        await log_and_delete(sent, context)
        return AGENT_COUNT

async def police_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['agents'][-1]['police_type'] = update.message.text
    sent = await update.message.reply_text("Nombre d'agents? ")
    await log_and_delete(sent, context)
    return AGENT_COUNT

async def agent_other_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['agents'][-1]['details'] = update.message.text
    sent = await update.message.reply_text("Nombre d'agents? ")
    await log_and_delete(sent, context)
    return AGENT_COUNT

async def agent_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['agents'][-1]['count'] = update.message.text
    sent = await update.message.reply_text(
        "Autre type d'agent supplémentaire?",
        reply_markup=ReplyKeyboardMarkup(keyboard_yes_no, one_time_keyboard=True)
    )
    await log_and_delete(sent, context)
    return OTHER_AGENT_YN

async def other_agent_yn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    text = update.message.text
    # On vérifie la présence de 'Oui' dans le texte pour gérer le choix Oui/Non
    if 'Oui' in text:
        sent = await update.message.reply_text(
            "Quel type d'agent?",
            reply_markup=ReplyKeyboardMarkup(keyboard_agent, one_time_keyboard=True)
        )
        await log_and_delete(sent, context)
        return TYPE_AGENT
    # Si l'utilisateur répond Non ou autre, on passe à l'intervention
    sent = await update.message.reply_text(
        "Quel est le type d'intervention?",
        reply_markup=ReplyKeyboardMarkup(keyboard_intervention, one_time_keyboard=True)
    )
    await log_and_delete(sent, context)
    return INTERVENTION_TYPE

async def intervention_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    itype = update.message.text
    context.user_data['intervention_type'] = itype
    if itype == 'Contrôle':
        sent = await update.message.reply_text(
            "Quel type?",
            reply_markup=ReplyKeyboardMarkup(keyboard_control, one_time_keyboard=True)
        )
        await log_and_delete(sent, context)
        return CONTROL_TYPE
    elif itype == 'Agression':
        sent = await update.message.reply_text("Précisez le type d'agression? ")
        await log_and_delete(sent, context)
        return AGGRESSION_DETAIL
    else:
        return await ask_target_and_issue(update, context)

async def control_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['control_type'] = update.message.text
    return await ask_target_and_issue(update, context)

async def aggression_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['aggression_detail'] = update.message.text
    return await ask_target_and_issue(update, context)

async def ask_target_and_issue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sent = await update.message.reply_text("Nombre de personnes ciblées? ")
    await log_and_delete(sent, context)
    return TARGET_COUNT

async def target_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['target_count'] = update.message.text
    sent = await update.message.reply_text(
        "Quelle est l'issue? (Restez sur place si possible)",
        reply_markup=ReplyKeyboardMarkup(keyboard_issue, one_time_keyboard=True)
    )
    await log_and_delete(sent, context)
    return ISSUE

async def issue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['issue'] = update.message.text
    # Nouvelle question ajoutée après ISSUE
    sent = await update.message.reply_text(
        "Qu'avez-vous pu transmettre ? (tract autodéfense / témoins / nom d'avocat, etc.) (Sinon envoyez \".\" )",
        reply_markup=ReplyKeyboardMarkup([], one_time_keyboard=True)
    )
    await log_and_delete(sent, context)
    return TRANSMISSION

async def transmission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    # Stocke la réponse libre
    context.user_data['transmissions'] = update.message.text
    # On poursuit avec la suite : témoin direct
    sent = await update.message.reply_text(
        "Êtes-vous témoin direct?",
        reply_markup=ReplyKeyboardMarkup(keyboard_yes_no, one_time_keyboard=True)
    )
    await log_and_delete(sent, context)
    return WITNESS_YN

async def witness_yn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    text = update.message.text
    if text == 'Non':
        sent = await update.message.reply_text(
            "Si ce n'est pas compromettant précisez la source, sinon écrire \"non\""
        )
        await log_and_delete(sent, context)
        return WITNESS_SOURCE
    return await ask_contact(update, context)
async def witness_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['witness_source'] = update.message.text
    return await ask_contact(update, context)

async def ask_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sent = await update.message.reply_text(
        "Merci beaucoup, votre signalement a été transmis. Souhaitez·vous pouvoir être recontacté·e si besoin de plus de renseignements?",
        reply_markup=ReplyKeyboardMarkup(keyboard_yes_no, one_time_keyboard=True)
    )
    await log_and_delete(sent, context)
    return CONTACT_YN

async def contact_yn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await log_and_delete(update.message, context)
    context.user_data['contact'] = update.message.text
    save_report(context.user_data)
    await delete_all(context)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_all(context)
    return ConversationHandler.END


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Erreur : TELEGRAM_BOT_TOKEN n'est pas défini dans les variables d'environnement.")
    app = ApplicationBuilder().token(token).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(filters.Regex(r'Start'), handle_start)],
        states={
            START: [MessageHandler(filters.Regex(r'Start'), handle_start)],
            LOCATION_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, location_type)],
            TRANSPORT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, transport_type)],
            TRAIN_STATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, train_station)],
            METRO_STATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, metro_station)],
            BUS_STOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, bus_stop)],
            LOCATION_DETAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, location_detail)],
            OTHER_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, other_location)],
            TIME_DELTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_delta)],
            TYPE_AGENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_agent)],
            POLICE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, police_type)],
            AGENT_OTHER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, agent_other_text)],
            AGENT_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, agent_count)],
            OTHER_AGENT_YN: [MessageHandler(filters.TEXT & ~filters.COMMAND, other_agent_yn)],
            INTERVENTION_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, intervention_type)],
            CONTROL_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, control_type)],
            AGGRESSION_DETAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, aggression_detail)],
            TARGET_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, target_count)],
            ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, issue)],
            TRANSMISSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, transmission)],
            WITNESS_YN: [MessageHandler(filters.TEXT & ~filters.COMMAND, witness_yn)],
            WITNESS_SOURCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, witness_source)],
            CONTACT_YN: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_yn)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == '__main__':
    main()
