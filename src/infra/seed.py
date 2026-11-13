from src.domain.models import Stop, StopStatus

SEED_STOPS = [
    Stop("pt-001", "Avenida Paulista", ("875A-10", "702U-10"), StopStatus.OPERATING),
    Stop("pt-002", "Terminal Bandeira", ("5121-10", "917H-10", "N631-11"), StopStatus.DELAYED,
         note="Intervalo médio de 18 min por obras na via"),
    Stop("pt-003", "Praça da Sé", ("1018-10", "407Y-10"), StopStatus.SUSPENDED,
         alternative_stop_id="pt-004", note="Desvio por evento até as 18h"),
    Stop("pt-004", "Largo São Francisco", ("1018-10", "775C-10"), StopStatus.OPERATING),
    Stop("pt-005", "Estação Pinheiros", ("8700-10", "7725-10"), StopStatus.OPERATING),
    Stop("pt-006", "Terminal Santo Amaro", ("6291-10", "6414-10"), StopStatus.DELAYED,
         note="Fila de embarque acima do normal"),
    Stop("pt-007", "Rua Augusta", ("N604-11",), StopStatus.SUSPENDED,
         alternative_stop_id="pt-001", note="Ponto desativado para obras"),
]
