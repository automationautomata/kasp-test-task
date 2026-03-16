import asyncio
import logging

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.models import ChunkReader
from app.services import (
    ExportFormats,
    StatisticsExporter,
    StatisticsExporterError,
    WordFormStatistics,
    WordFormStatisticsError,
)

router = APIRouter(route_class=DishkaRoute)

ChunkSizeMB = int


@router.post("/public/report/export")
async def handler(
    file: UploadFile,
    semaphore: FromDishka[asyncio.Semaphore],
    word_form_stat: FromDishka[WordFormStatistics],
    stat_exporter: FromDishka[StatisticsExporter],
    upload_chunk_size: FromDishka[ChunkSizeMB],
    logger: FromDishka[logging.Logger],
):
    async with semaphore:
        try:
            reader = ChunkReader(file, upload_chunk_size)
            key = await word_form_stat.collect_statistics(reader)
            writer = await stat_exporter.export(key, ExportFormats.XLSX)
            return StreamingResponse(writer)

        except StatisticsExporterError as e:
            logger.exception(f"Export statistics failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Export statistics failed"},
            )

        except WordFormStatisticsError as e:
            logger.exception(f"Text processing failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Text processing failed"},
            )


@router.get("/health")
def health_check():
    return {"status": "healthy"}
