import requests
from django.conf import settings

from insights.internals.base import InternalAuthentication
from insights.sources.clients import GenericSQLQueryGenerator


class AgentSQLQueryGenerator(GenericSQLQueryGenerator):
    default_query_type = "list"


class AgentsRESTClient(InternalAuthentication):
    def __init__(self, project) -> None:
        self.project = project
        self.url = (
            f"{settings.CHATS_URL}/v1/internal/dashboard/{self.project.uuid}/agent/"
        )

    def list(self, query_filters: dict):
        if query_filters.get("created_on__gte", None):
            query_filters["start_date"] = query_filters.pop("created_on__gte")
        if query_filters.get("created_on__lte", None):
            query_filters["end_date"] = query_filters.pop("created_on__lte")
        
        # Imprimir para debug
        print(f"Enviando requisição para: {self.url}")
        print(f"Parâmetros: {query_filters}")
        
        response = requests.get(
            url=self.url, headers=self.headers, params=query_filters
        )
        
        # Verificar status da resposta
        print(f"Status da resposta: {response.status_code}")
        
        # Tentar processar a resposta com tratamento de erro
        try:
            if response.status_code >= 400:
                print(f"Erro no servidor: {response.status_code}")
                print(f"Conteúdo da resposta: {response.text[:500]}")  # Mostrar os primeiros 500 caracteres
                return {"error": f"Server error: {response.status_code}"}
                
            if not response.text.strip():
                print("Resposta vazia do servidor")
                return {}
                
            return response.json()
        except requests.exceptions.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {str(e)}")
            print(f"Conteúdo da resposta: {response.text[:500]}")  # Mostrar os primeiros 500 caracteres
            return {"error": "Invalid server response"}
