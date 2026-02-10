"""내보내기 API 엔드포인트

위치: app/api/routes/export.py
- NL2SQL 조회 결과를 Excel 파일로 내보내기
"""
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.services.export_service import export_service
from app.core.errors import APIException, ErrorCode
from app.models.search import ExcelExportRequest
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/export", tags=["export"])


@router.post("/excel")
async def export_excel(request: ExcelExportRequest):
    """NL2SQL 조회 결과를 Excel 파일로 내보내기"""
    try:
        output = export_service.generate_excel(
            columns=request.columns,
            rows=request.rows,
            question=request.question or "",
            sql=request.sql or "",
            answer=request.answer or "",
            execution_time_ms=request.execution_time_ms or 0,
        )

        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        encoded_filename = quote(filename)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )

    except Exception as e:
        logger.error(f"Excel 내보내기 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))
