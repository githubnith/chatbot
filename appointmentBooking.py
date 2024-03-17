from openai import OpenAI
from time import sleep
import json

client = OpenAI()
starting_assistant = ""
appointment_thread = ""

appointment_tools = [{
    "type": "function",
        "function": {
            "name": "askWhichDoctor",
            "description": "Ask which doctor to book appointment with",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the doctor to book appointment with"}
                },
                "required": ["name"],
            }
        }
}, {
    "type": "function",
        "function": {
            "name": "askWhatTime",
            "description": "Ask what time to book appointment with doctor",
            "parameters": {
                "type": "object",
                "properties": {
                    "time": {"type": "string", "description": "Time to book appointment with doctor"}
                },
                "required": ["time"],
            }
        }
}]

def create_assistant():
    if starting_assistant == "":
        appointment_assistant = client.beta.assistants.create(
        name="Appointment Booking Assistant for Super Clinic Health Center",
        model="gpt-3.5-turbo-16k-0613",
        instructions="You are an appointment booking assistant for the Super Clinc Health Center. You can help users book appointments, cancel appointments, and get information about their appointments. There are 2 doctors namely Dr. Ruth and Dr. Sam, who work from 9AM to 5PM, Monday to Friday.",
        tools=appointment_tools
        )
    else:
        appointment_assistant = client.beta.assistants.retrieve(starting_assistant)
    return appointment_assistant

def get_doctor_name(name):
    return f"The doctor {name} is available."

def get_doctor_availability(time):
    return f"The time {time} is available." 

def create_thread():
    empty_thread = client.beta.threads.create()
    return empty_thread

def create_message(thread_id, message):
    thread_message = client.beta.threads.messages.create(
        thread_id,
        role="user",
        content=message,
    )
    return thread_message

def run_assistant(thread_id, assistant_id):
    run = client.beta.threads.runs.create(
        thread_id=thread_id, assistant_id=assistant_id
    )
    return run

def get_run_status(thread_id, run_id):
    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
    return run.status

def greet():
    return "Hello! Welcome to the Super Clinic Health Center. How can I help you today? : "

def get_newest_message(thread_id):
    thread_messages = client.beta.threads.messages.list(thread_id)
    return thread_messages.data[0]

def run_action(thread_id, run_id):
    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

    for tool in run.required_action.submit_tool_outputs.tool_calls:

        if tool.function.name == "askWhichDoctor":
            arguments = json.loads(tool.function.arguments)
            name = arguments["name"]

            doctor_info = get_doctor_name(name)

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=[
                    {
                        "tool_call_id": tool.id,
                        "output": doctor_info,
                    },
                ],
            )
        elif tool.function.name == "askWhatTime":
            arguments = json.loads(tool.function.arguments)
            time = arguments["time"]

            availability_info = get_doctor_availability(time)

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=[
                    {
                        "tool_call_id": tool.id,
                        "output": availability_info,
                    },
                ],
            )
        else:
            raise Exception(
                f"Unsupported function call: {tool.function.name} provided."
            )
        
def main():
    my_assistant = create_assistant()
    my_thread = create_thread()
    print(greet() + '\n')

    while True:
        user_message = input(': ')
        if user_message.lower() == "exit":
            break

        create_message(my_thread.id, user_message)
        run = run_assistant(my_thread.id, my_assistant.id)

        while run.status != "completed":
            run.status = get_run_status(my_thread.id, run.id)

            # If assistant needs to call a function, it will enter the "requires_action" state
            if run.status == "requires_action":
                run_action(my_thread.id, run.id)

            sleep(1)
            print("⏳", end="\r", flush=True)

        sleep(0.5)

        response = get_newest_message(my_thread.id)
        print(response.content[0].text.value)


if __name__ == "__main__":
    main()