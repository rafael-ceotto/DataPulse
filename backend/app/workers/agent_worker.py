import asyncio
from app.core.sqs import receive_messages, delete_message
from app.core.job_store import set_job_processing, set_job_done, set_job_failed
from app.core.database import AsyncSessionLocal
from app.ai.hospital_agent_service import ask_agent
from app.core.logging import logger


async def process_message(message: dict) -> None:
    job_id = message["job_id"]
    question = message["question"]
    receipt_handle = message["receipt_handle"]
    username = message.get("username", "admin")
    conversation_id = message.get("conversation_id", None)

    await set_job_processing(job_id)
    logger.info("agent_worker_processing", job_id=job_id, question=question)

    try:
        async with AsyncSessionLocal() as session:
            result = await ask_agent(session, question, username=username, conversation_id=conversation_id)
        await set_job_done(job_id, result)
        await delete_message(receipt_handle)

        from app.core.cost_tracker import record_query_cost
        tokens = result.get("tokens_used", {})
        if tokens.get("total", 0) > 0:
            await record_query_cost(
                username,
                tokens.get("prompt", 0),
                tokens.get("completion", 0),
            )

        logger.info("agent_worker_done", job_id=job_id)
    except Exception as e:
        logger.error("agent_worker_failed", job_id=job_id, error=str(e))
        await set_job_failed(job_id, str(e))
        await delete_message(receipt_handle)


async def run_worker() -> None:
    logger.info("agent_worker_started")
    while True:
        try:
            messages = await receive_messages(max_messages=1)
            if messages:
                for message in messages:
                    await process_message(message)
            else:
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            logger.info("agent_worker_stopped")
            break
        except Exception as e:
            logger.error("agent_worker_error", error=str(e))
            await asyncio.sleep(5)