import time, json
import MetaTrader5 as mt5
from openai import OpenAI
from datetime import datetime
import configparser

def get_today():
    return int(datetime.now().timestamp())

def timestamp_to_human(timestamp: int):
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d') #'%Y-%m-%d %H:%M:%S'

def get_forex_rates(symbol: str, timeframe: str, from_date: int, to_date: int):
    print(f"symbol: {symbol}, timeframe: {timeframe}, from_date: {from_date}, to_date: {to_date}")
    if not mt5.initialize():
        print("initialize() failed")
        mt5.shutdown()

    timeframe_mt5 = 0
    if timeframe == "TIMEFRAME_M5": timeframe_mt5 = mt5.TIMEFRAME_M5
    elif timeframe == "TIMEFRAME_H1": timeframe_mt5 = mt5.TIMEFRAME_H1
    elif timeframe == "TIMEFRAME_D1": timeframe_mt5 = mt5.TIMEFRAME_D1
    elif timeframe == "TIMEFRAME_W1": timeframe_mt5 = mt5.TIMEFRAME_W1

    rates = mt5.copy_rates_range(symbol, timeframe_mt5, from_date, to_date)
    mt5.shutdown()
    return rates

def show_json(obj):
    print(json.dumps(json.loads(obj.model_dump_json()), indent=4))

client = OpenAI()

def create_assistent():
    assistant = client.beta.assistants.create(
        name="Forex Advisor",
        instructions="You know everything about the forex and financial markets. You are very good in calculations of levels of support and resistance. " \
                     "Answer in the language of the request. " \
                     "Before doing anything - get the current time with the tool get_today. " \
                     "Call the tool get_today only once - at the beginning. " \
                     "The current day is always the day, gotten from the tool get_today. " \
                     "For the dates, shown in the answer, use only human readible date and not the unix one. " \
                     "If you are not sure about the name of the ticket, ask the user " \
                     "Mandatory show 3 levels of support and resistance as well as the used dates. ",
        model="gpt-4-1106-preview",
        tools=[{
            "type": "function",
            "function": {
                "name": "get_forex_rates",
                "description": "Get the rates of forex currency pairs, as well as other financial instruments. " \
                               "Many instruments are supported - if you are not sure about the name of the ticket - ask the user. " \
                               "The tool returns array of arrays. " \
                               "Each element of the inner array represent the followed data: " \
                                "0 - Datatime in unix format. " \
                                "1 - open, " \
                                "2 - high, " \
                                "3 - low, " \
                                "4 - close, " \
                                "5 - tick_volume, " \
                                "6 - spread, " \
                                "7 - real_volume" \
                                "If the result is empty, try to call it again for one day earlier. " \
                                "The empty result may  " \
                                "Repeat until get a result, but no more than 5 days. ",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The name of the market ticket e.g. EURUSD, USDJPY, GOLD, AVGO etc. " \
                                            "In case of doubt ask the user " \
                        },
                        "timeframe": {
                            "type": "string",
                            "description": "The used timeframe",
                            "enum": [
                                "TIMEFRAME_M5",
                                "TIMEFRAME_H1",
                                "TIMEFRAME_D1",
                                "TIMEFRAME_W1"
                            ]
                        },
                        "from_date": {
                            "type": "integer",
                            "description": "Start date and time in unix format - i.e. number of seconds elapsed since 1970.01.01",
                        },
                        "to_date": {
                            "type": "integer",
                            "description": "End date and time in unix format - i.e. number of seconds elapsed since 1970.01.01",
                        },
                    },
                    "required": [
                        "symbol",
                        "timeframe",
                        "from_date",
                        "to_date"
                    ]
                }
            }
        },{
            "type": "function",
            "function": {
                "name": "timestamp_to_human",
                "description": "Use it to convert unix date to string in your answer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timestamp": {
                            "type": "integer",
                            "description": "the timestamp - i.e. the unix date - number of seconds elapsed since 1970.01.01"
                        }
                    },
                    "required": [
                        "timestamp"
                    ]
                }
            }
        },{
            "type": "function",
            "function": {
                "name": "get_today",
                "description": "Get the current time in unix format. Use it every time you need to know the current time"
            }
        }]
    )
    show_json(assistant)
    return assistant.id

def check_assistant_exists():
    config = configparser.ConfigParser()
    config.read('config.ini')
    try:
        assistant_id = config.get("Default", "assistant_id")
    except:
        print("Assistant not found. Create one.")

        assistant_id = create_assistent()

        if not config.has_section("Default"):
            config.add_section("Default")
        config.set("Default", "assistant_id", assistant_id)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        return assistant_id
    else:
        print(f"Found assistant: {assistant_id}")
        return assistant_id

def requires_action(run, thread):
    tool_outputs =[]
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        print(json.dumps(arguments, indent=4))

        if name == "get_forex_rates":
            responses = get_forex_rates(arguments["symbol"], arguments["timeframe"], arguments["from_date"], arguments["to_date"])
            print(json.dumps(responses.tolist(), indent=4))
            responses = json.dumps(responses.tolist())
        elif name == "get_today":
            responses = get_today()
            print(f"Current time unix: {responses}")
        elif name == "timestamp_to_human":
            responses = timestamp_to_human(arguments["timestamp"])
            print(f"Unix time {arguments['timestamp']} = {responses}")

        tool_outputs.append(
            {
                "tool_call_id": tool_call.id,
                "output": responses,
            }
        )

    run = client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread.id,
        run_id=run.id,
        tool_outputs=tool_outputs,
    )
    print(f"Run status: {run.status}")

def wait_on_run(assistant_id, thread, user_input):
    run = submit_message(assistant_id, thread, user_input)
    while run.status == "queued" or run.status == "in_progress" or run.status == "requires_action":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        if run.status == "requires_action":
            requires_action(run, thread)
        time.sleep(0.5)
    return run

def submit_message(assistant_id, thread, user_message):
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_message
    )
    return client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )

def get_response(thread):
    return client.beta.threads.messages.list(thread_id=thread.id, order="asc")

def create_thread_and_run(user_input):
    thread = client.beta.threads.create()
    run = submit_message(assistant_id, thread, user_input)
    return thread, run

def pretty_print(messages):
    print("# Messages")
    for m in messages:
        print(f"{m.role}: {m.content[0].text.value}")
    print()

assistant_id = check_assistant_exists()
try:
    thread = client.beta.threads.create()
    while True:
        user_input = input("Your question: ")
        run = wait_on_run(assistant_id, thread, user_input)
        pretty_print(get_response(thread))
except:
    print("Bye")
finally:
    print("Thank you for your questions!")
    client.beta.threads.delete(thread.id)
