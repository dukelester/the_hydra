from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.services.search import search_civic_data


class SearchAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "")
        results = search_civic_data(query, limit=10)
        return Response(
            {
                "query": results["query"],
                "total": results["total"],
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
