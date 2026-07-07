from insights.metrics.meta.clients import MetaGraphAPIClient


class GetTemplatesFromPrefixUseCase:
    def __init__(self, meta_client: MetaGraphAPIClient | None = None):
        self.meta_client = meta_client or MetaGraphAPIClient()

    def execute(
        self,
        waba_id: str,
        prefix: str,
        max_template_ids: int | None = None,
    ) -> list[str]:
        response = self.meta_client.get_templates_list(
            waba_id=waba_id, name=prefix
        )
        data = response.get("data", [])
        matched = [
            tpl for tpl in data if tpl.get("name", "").startswith(prefix)
        ]

        if max_template_ids is not None:
            matched = sorted(matched, key=lambda tpl: tpl["name"], reverse=True)
            matched = matched[:max_template_ids]

        return [tpl["id"] for tpl in matched]
