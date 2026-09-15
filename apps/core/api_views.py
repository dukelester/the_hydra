from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.governance import request_country
from apps.core.services.search import search_civic_data


class SearchAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "")
        try:
            limit = min(max(int(request.query_params.get("limit") or 10), 1), 25)
        except (TypeError, ValueError):
            limit = 10
        suggest = request.query_params.get("suggest", "").lower() in {"1", "true", "yes"}
        results = search_civic_data(
            query,
            limit=limit,
            kind=request.query_params.get("kind", "all"),
            county=request.query_params.get("county", ""),
            status=request.query_params.get("status", ""),
            category=request.query_params.get("category", ""),
            country=request_country(request),
            suggest=suggest,
        )
        return Response(
            {
                "query": results["query"],
                "kind": results["kind"],
                "too_short": results["too_short"],
                "total": results["total"],
                "project_count": results["project_count"],
                "institution_count": results["institution_count"],
                "policy_count": results["policy_count"],
                "document_count": results["document_count"],
                "projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "slug": p.slug,
                        "county": p.county,
                        "status": p.status,
                    }
                    for p in results["projects"]
                ],
                "institutions": [
                    {"id": i.id, "name": i.name, "slug": i.slug} for i in results["institutions"]
                ],
                "policies": [
                    {"id": p.id, "title": p.title, "slug": p.slug} for p in results["policies"]
                ],
                "documents": [
                    {"id": d.id, "title": d.title, "publisher": d.publisher}
                    for d in results["documents"]
                ],
            }
        )
