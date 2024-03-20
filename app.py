from dotenv import load_dotenv
import chainlit
from langchain.agents import (
    create_openai_tools_agent,
    AgentExecutor,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.exceptions import OutputParserException
from langchain_openai import ChatOpenAI
from tools.aws.cost_explorer_tool import AwsCostExplorerTool
from tools.aws.ec2_tool import AwsEc2Tool
from tools.aws.iam_tool import AwsIamTool
from tools.aws.s3_tool import AwsS3Tool


def parsing_error_handler(_: OutputParserException) -> str:
    return "Apologies, an error was encountered when interpreting the input. Please attempt again, perhaps with a rephrased question."


def set_up_agent_executor() -> AgentExecutor:
    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
    tools = [AwsS3Tool(), AwsEc2Tool(), AwsIamTool(), AwsCostExplorerTool()]
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant who has knowledge about a variety of AWS resources in an AWS account.",
            ),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_openai_tools_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=parsing_error_handler,
    )


@chainlit.on_chat_start
def on_chat_start():
    agent_executor = set_up_agent_executor()
    chainlit.user_session.set("agent_executor", agent_executor)

    print("A new chat session has started!")


@chainlit.on_message
async def on_message(message: chainlit.Message):
    agent_executor: AgentExecutor = chainlit.user_session.get("agent_executor")
    response = agent_executor.invoke({"input": message.content})
    await chainlit.Message(content=response["output"]).send()


if __name__ == "__main__":
    load_dotenv()
