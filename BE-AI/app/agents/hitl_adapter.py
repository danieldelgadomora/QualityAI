from agente_v4_hitl import RequirementsRefinerAgent as _HITLBase


class APIRequirementsRefinerAgent(_HITLBase):
    """Subclase de agente v4 que reemplaza input() por resoluciones inyectadas vía API.

    Uso:
        agent = APIRequirementsRefinerAgent(groq_api_key=...)

        # Fase 1 — detección (acceso directo al detector, sin LLM)
        ambiguities = agent.ambiguity_detector.analyze(requirement_text)

        # Fase 2 — pipeline completo con resoluciones del analista
        result = agent.process_with_resolutions(
            requirement=requirement_text,
            top_k=top_k,
            resolutions=[
                {"word": "seguro", "category": "adjetivo_vago",
                 "analyst_resolution": "cifrado AES-256 + 2FA", "status": "resolved"},
                {"word": "rápido", "category": "adjetivo_vago",
                 "analyst_resolution": "", "status": "dismissed"},
            ],
        )
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._injected_resolutions: list[dict] | None = None

    def _review_ambiguities_with_analyst(
        self, ambiguities: list
    ) -> tuple[list[dict], list[str]]:
        """Override: usa resoluciones pre-inyectadas en vez de input()."""
        resolutions = self._injected_resolutions or []
        clarifications = [
            f'- "{r["word"]}": {r["analyst_resolution"]}'
            for r in resolutions
            if r.get("status") == "resolved" and r.get("analyst_resolution")
        ]
        return resolutions, clarifications

    def process_with_resolutions(
        self,
        requirement: str,
        top_k: int,
        resolutions: list[dict],
    ):
        """Ejecuta el pipeline completo usando las resoluciones del analista.

        Equivalente a process(interactive=True) pero sin bloquear en input().
        Las resoluciones se limpian tras la ejecución para evitar filtraciones
        entre llamadas concurrentes (el asyncio.Lock en el servicio garantiza
        que solo una llamada use la instancia a la vez).
        """
        self._injected_resolutions = resolutions
        try:
            return self.process(requirement, top_k=top_k, interactive=True)
        finally:
            self._injected_resolutions = None
