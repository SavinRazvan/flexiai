# flexiai/core/flexiai_client.py
import time
import json
import logging
from openai import OpenAIError
from flexiai.config.logging_config import setup_logging
from flexiai.assistant.task_manager import TaskManager
from flexiai.assistant.function_mapping import get_function_mappings, register_user_functions
from flexiai.credentials.credential_manager import CredentialManager

# Set up logging using your custom configuration
setup_logging(root_level=logging.WARNING, file_level=logging.WARNING, console_level=logging.ERROR)


class FlexiAI:
    """
    FlexiAI is a flexible AI framework for managing interactions with OpenAI and
    Azure OpenAI services. It supports dynamic creation and management of threads,
    adding user messages, and running threads with specified assistants, handling
    required actions and logging all activities.

    Attributes:
        logger (logging.Logger): Logger for logging information and errors.
        client (OpenAI or AzureOpenAI): Client for interacting with OpenAI or Azure
        OpenAI services.
        task_manager (TaskManager): Manages tasks and their execution.
        personal_function_mapping (dict): Mapping of function names to their personal
        function implementations.
        assistant_function_mapping (dict): Mapping of function names to their assistant
        function implementations.
    """

    def __init__(self):
        """
        Initializes the FlexiAI instance by setting up logging, determining the
        credential type, and initializing the appropriate OpenAI or Azure OpenAI client. 
        Also sets up task management and function mappings.
        """
        # Initialize the logger for this class
        self.logger = logging.getLogger(__name__)

        # Initialize the credential manager and get the client
        self.credential_manager = CredentialManager()
        self.client = self.credential_manager.client

        # Initialize the task manager
        self.task_manager = TaskManager()

        # Get the function mappings for personal functions and assistant calling functions
        self.personal_function_mapping, self.assistant_function_mapping = get_function_mappings()

        # Register user functions
        self.personal_function_mapping, self.assistant_function_mapping = register_user_functions(
            self.personal_function_mapping,
            self.assistant_function_mapping
        )

    def create_thread(self):
        """
        Create a new thread.

        Returns:
            object: The newly created thread object.

        Raises:
            OpenAIError: If the API call to create a new thread fails.
            Exception: If an unexpected error occurs.
        """
        try:
            self.logger.info("Creating a new thread")
            thread = self.client.beta.threads.create()
            self.logger.info(f"Created thread with ID: {thread.id}")
            return thread
        except OpenAIError as e:
            self.logger.error(f"Failed to create a new thread: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while creating a thread: {str(e)}", exc_info=True)
            raise


    def add_user_message(self, thread_id, user_message):
        """
        Add a user message to a specified thread.

        Args:
            thread_id (str): The ID of the thread.
            user_message (str): The user's message content.

        Returns:
            object: The message object that was added to the thread.

        Raises:
            OpenAIError: If the API call to add a user message fails.
            Exception: If an unexpected error occurs.
        """
        try:
            self.logger.info(f"Adding user message to thread {thread_id}: {user_message}")
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_message
            )
            self.logger.info(f"Added user message with ID: {message.id}")
            return message
        except OpenAIError as e:
            self.logger.error(f"Failed to add a user message to the thread {thread_id}: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while adding a user message to thread {thread_id}: {str(e)}", exc_info=True)
            raise


    def wait_for_run_completion(self, thread_id):
        """
        Wait for any active run in the thread to complete.

        Args:
            thread_id (str): The ID of the thread.

        Raises:
            OpenAIError: If the API call to retrieve thread runs fails.
            Exception: If an unexpected error occurs.
        """
        try:
            while True:
                self.logger.info(f"Checking for active runs in thread {thread_id}")
                runs = self.client.beta.threads.runs.list(thread_id=thread_id)
                active_runs = [run for run in runs if run.status in ["queued", "in_progress", "cancelling"]]
                if active_runs:
                    self.logger.info(
                        f"Run {active_runs[0].id} is currently {active_runs[0].status}. ""Waiting for completion...")
                    time.sleep(1)  # Wait for 1 second before checking again
                else:
                    self.logger.info(
                        f"No active run in thread {thread_id}. Proceeding...")
                    break
        except OpenAIError as e:
            self.logger.error(f"Failed to retrieve thread runs for thread {thread_id}: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while waiting for run completion in thread {thread_id}: {str(e)}", exc_info=True)
            raise


    def create_run(self, assistant_id, thread_id):
        """
        Create and run a thread with the specified assistant, handling required actions.

        Args:
            assistant_id (str): The ID of the assistant.
            thread_id (str): The ID of the thread.

        Returns:
            object: The run object.

        Raises:
            OpenAIError: If any API call within this function fails.
            Exception: If an unexpected error occurs.
        """
        try:
            self.logger.info(f"Starting a new run for thread {thread_id} with assistant {assistant_id}")
            
            # Wait for any active run to complete
            self.wait_for_run_completion(thread_id)
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id, assistant_id=assistant_id
            )

            # Monitor the status of the run
            while run.status in ['queued', 'in_progress', 'cancelling', 'requires_action']:
                self.logger.info(f"Run status: {run.status}")
                if run.status == 'requires_action':
                    self.handle_requires_action(run, assistant_id, thread_id)
                time.sleep(1)  # Wait for 1 second before checking again
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id, run_id=run.id
                )

            # Check the final status of the run
            if run.status == 'completed':
                self.logger.info(f"Run {run.id} completed successfully for thread {thread_id}")
                return run
            else:
                self.logger.error(f"Run {run.id} failed with status: {run.status}")
                return None
        except OpenAIError as e:
            self.logger.error(f"An error occurred during thread run for thread {thread_id} with assistant {assistant_id}: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during thread run for thread {thread_id} with assistant {assistant_id}: {str(e)}", exc_info=True)
            raise


    def create_advanced_run(self, assistant_id, thread_id, user_message):
        """
        Create and run a thread with the specified assistant, user message and handling
        required actions.

        Args:
            assistant_id (str): The ID of the assistant.
            thread_id (str): The ID of the thread.
            user_message (str): The user's message content.

        Returns:
            object: The run object.

        Raises:
            OpenAIError: If any API call within this function fails.
            Exception: If an unexpected error occurs.
        """
        try:
            self.logger.info(f"Starting a new run for thread {thread_id} with assistant {assistant_id}")
            
            # Wait for any active run to complete
            self.wait_for_run_completion(thread_id)
            
            # Add the user's message to the thread
            self.add_user_message(thread_id, user_message)
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id, assistant_id=assistant_id
            )

            # Monitor the status of the run
            while run.status in ['queued', 'in_progress', 'cancelling', 'requires_action']:
                self.logger.info(f"Run status: {run.status}")
                if run.status == 'requires_action':
                    self.handle_requires_action(run, assistant_id, thread_id)
                time.sleep(1)  # Wait for 1 second before checking again
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id, run_id=run.id
                )

            # Check the final status of the run
            if run.status == 'completed':
                self.logger.info(f"Run {run.id} completed successfully for thread {thread_id}")
            else:
                self.logger.error(f"Run {run.id} failed with status: {run.status}")

            return run
        except OpenAIError as e:
            self.logger.error(f"An error occurred during thread run for thread {thread_id} with assistant {assistant_id}: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during thread run for thread {thread_id} with assistant {assistant_id}: {str(e)}", exc_info=True)
            raise


    def retrieve_messages(self, thread_id, order='desc', limit=20):
        """
        Retrieve the message objects from a specified thread.

        Args:
            thread_id (str): The ID of the thread.
            order (str, optional): The order in which to retrieve messages, either 'asc' or 'desc'. Defaults to 'desc'.
            limit (int, optional): The number of messages to retrieve. Defaults to 20.

        Returns:
            list: A list of dictionaries containing the message ID, role, and content
            of each message.

        Raises:
            OpenAIError: If the API call to retrieve messages fails.
            Exception: If an unexpected error occurs.
        """
        try:
            params = {'order': order, 'limit': limit}
            response = self.client.beta.threads.messages.list(thread_id=thread_id, **params)
            if not response.data:
                self.logger.info("No data found in the response or no messages.")
                return []

            self.logger.info(f"Retrieved {len(response.data)} messages from thread {thread_id}")
            messages = response.data[::-1]
            formatted_messages = []

            for message in messages:
                message_id = message.id
                role = message.role
                content_blocks = message.content
                content_value = " ".join([
                    block.text.value for block in content_blocks if hasattr(block, 'text') and hasattr(block.text, 'value')
                ])

                self.logger.info(f"Message ID: {message_id}, Role: {role}, Content: {content_blocks}")

                formatted_messages.append({
                    'message_id': message_id,
                    'role': role,
                    'content': content_value
                })

            return formatted_messages
        except OpenAIError as e:
            self.logger.error(f"Failed to fetch messages for thread {thread_id}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while fetching messages: {str(e)}")
            raise


    def retrieve_message_object(self, thread_id, order='asc', limit=20):
        """
        Retrieve the message objects from a specified thread.

        Args:
            thread_id (str): The ID of the thread.
            order (str, optional): The order in which to retrieve messages, either 'asc' or 'desc'. Defaults to 'asc'.
            limit (int, optional): The number of messages to retrieve. Defaults to 20.

        Returns:
            list: A list of message objects.

        Raises:
            OpenAIError: If the API call to retrieve messages fails.
            Exception: If an unexpected error occurs.
        """
        try:
            params = {'order': order, 'limit': limit}
            response = self.client.beta.threads.messages.list(thread_id=thread_id, **params)
            if not response.data:
                self.logger.info("No data found in the response or no messages.")
                return []

            self.logger.info(f"Retrieved {len(response.data)} messages from thread {thread_id}")
            messages = response.data
            return messages
        except OpenAIError as e:
            self.logger.error(f"Failed to fetch messages for thread {thread_id}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while fetching messages: {str(e)}")
            raise


    def process_and_print_messages(self, messages):
        """
        Process the message objects and print the role and content value of each message.

        Args:
            messages (list): The list of message objects.
        """
        for message in messages:
            role = "Assistant" if message.role == "assistant" else "User"
            content_blocks = message.content
            content_value = " ".join([
                block.text.value for block in content_blocks if hasattr(block, 'text') and hasattr(block.text, 'value')
            ])

            print(f"{role}: {content_value}")


    def handle_requires_action(self, run, assistant_id, thread_id):
        """
        Handle required actions from a run.

        This method processes the required actions for a given run. It executes the
        necessary functions and submits the outputs back to the OpenAI API or Azure
        OpenAI.

        Args:
            run (object): The run object requiring actions.
            assistant_id (str): The ID of the assistant.
            thread_id (str): The ID of the thread.

        Raises:
            OpenAIError: If an error occurs when interacting with the OpenAI API.
            Exception: If an unexpected error occurs during the process.
        """
        self.logger.info(f"Handling required action for run ID: {run.id} with assistant ID: {assistant_id}.")

        # Check if the run status indicates that actions are required
        if run.status == "requires_action":
            tool_outputs = []

            # Iterate over each tool call that requires an output submission
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                self.logger.info(f"Function Name: {function_name}")
                self.logger.info(f"Arguments: {arguments}")

                # Determine the type of action to perform
                action_type = self.determine_action_type(function_name)

                # Execute the appropriate function based on the action type
                if action_type == "call_assistant":
                    self.logger.info(f"Calling another assistant with arguments: {arguments}")
                    status, message, result = self.call_assistant_with_arguments(function_name, **arguments)
                else:
                    self.logger.info(f"Executing personal function with arguments: {arguments}")
                    status, message, result = self.execute_personal_function_with_arguments(function_name, **arguments)

                # Prepare the tool output for submission
                tool_output = {
                    "tool_call_id": tool_call.id,
                    "output": json.dumps({"status": status, "message": message, "result": result})
                }
                self.logger.info(f"Tool output to be submitted: {tool_output}")
                tool_outputs.append(tool_output)

            # Submit the tool outputs to the OpenAI API or Azure OpenAI
            try:
                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                self.logger.info(f"Successfully submitted tool outputs for run ID: {run.id}")
            except OpenAIError as e:
                self.logger.error(f"OpenAI API error when submitting tool outputs for run ID {run.id} in thread {thread_id} with assistant {assistant_id}: {str(e)}", exc_info=True)
                raise
            except Exception as e:
                self.logger.error(f"General error when submitting tool outputs for run ID {run.id} in thread {thread_id} with assistant {assistant_id}: {str(e)}", exc_info=True)
                raise
        else:
            self.logger.info(f"No required action for this run ID: {run.id}")


    def determine_action_type(self, function_name):
        """
        Determines the type of action required based on the function's name.

        Args:
            function_name (str): The name of the function.

        Returns:
            str: The type of action, either 'call_assistant' or 'personal_function'.
        """
        self.logger.info(f"Determining action type for function: {function_name}")
        if function_name.endswith("_assistant"):
            action_type = "call_assistant"
        else:
            action_type = "personal_function"
        self.logger.info(f"Action type for function {function_name}: {action_type}")
        return action_type


    def execute_personal_function_with_arguments(self, function_name, **arguments):
        """
        Dynamically executes a function from the function_mapping based on the provided
        function name and supplied arguments.

        Args:
            function_name (str): The name of the function to execute.
            **arguments: The arguments to pass to the function.

        Returns:
            tuple: A tuple containing the status (bool), message (str), and result (any).

        Raises:
            Exception: If the function execution fails.
        """
        self.logger.info(
            f"Attempting to execute function: {function_name} with arguments: {arguments}")
        func = self.personal_function_mapping.get(function_name, None)
        if callable(func):
            try:
                result = func(**arguments)
                self.logger.info(f"Personal Function {function_name} executed.")
                return True, "Action - Personal Function.", result
            except Exception as e:
                self.logger.error(
                    f"Error executing {function_name}: {str(e)}", exc_info=True)
                return False, f"Error executing {function_name}: {str(e)}", None
        else:
            self.logger.warning(f"Function {function_name} not found in mapping.")
            return False, f"Function not found: {function_name}", None


    def call_assistant_with_arguments(self, function_name, **arguments):
        """
        Routes the function call to the appropriate assistant or internal function.

        Args:
            function_name (str): The name of the function to call.
            **arguments: The arguments to pass to the function.

        Returns:
            tuple: A tuple containing the status (bool), message (str), and result (any).

        Raises:
            ValueError: If the function is not found.
            Exception: If the function execution fails.
        """
        self.logger.info(
            f"Attempting to dispatch an assistant using the function: {function_name} with arguments: {arguments}")
        func = self.assistant_function_mapping.get(function_name, None)
        if callable(func):
            try:
                result = func(**arguments)
                self.logger.info(f"Call Assistant Function {function_name} executed.")
                return True, "Action - Call Assistant.", result
            except Exception as e:
                self.logger.error(f"Error executing {function_name}: {str(e)}", exc_info=True)
                return False, f"Error executing {function_name}: {str(e)}", None
        else:
            error_message = f"Function {function_name} is not defined."
            self.logger.error(error_message)
            raise ValueError(error_message)
