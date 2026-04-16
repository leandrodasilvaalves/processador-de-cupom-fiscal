"""
Teste de exploração da condição de bug — Property 1: Bug Condition

CRÍTICO: Este teste DEVE FALHAR no código não corrigido.
A falha confirma que os bugs existem.

Validates: Requirements 1.1, 1.2, 1.3
"""

import sys
import os

# Garante que src/ está no path para importar os módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from entities.entitity import Entity
from entities.purchase import Purchase


# ---------------------------------------------------------------------------
# Geradores para Bug B — strings com separador de milhar no formato brasileiro
# ---------------------------------------------------------------------------

# Gera inteiros de 1 a 999 para a parte dos milhares
thousands = st.integers(min_value=1, max_value=999)
# Gera inteiros de 0 a 999 para a parte dos reais (sem milhar)
hundreds = st.integers(min_value=0, max_value=999)
# Gera inteiros de 0 a 99 para os centavos
cents = st.integers(min_value=0, max_value=99)


@st.composite
def brazilian_thousands_format(draw):
    """Gera strings no formato 'X.XXX,XX' com separador de milhar."""
    t = draw(thousands)       # parte dos milhares (1–999)
    h = draw(hundreds)        # parte dos reais (0–999)
    c = draw(cents)           # centavos (0–99)
    # Monta: "1.234,56"
    return f"{t}.{h:03d},{c:02d}"


# ---------------------------------------------------------------------------
# Bug B — _to_float com separador de milhar
# ---------------------------------------------------------------------------

class TestBugB_ToFloatWithThousandsSeparator:
    """
    **Validates: Requirements 1.2, 1.3**

    Bug B: _to_float("1.234,56") lança ValueError porque
    s.replace(",", ".") produz "1.234.56" — float inválido.

    Este teste DEVE FALHAR no código não corrigido.
    """

    @given(s=brazilian_thousands_format())
    @settings(max_examples=50)
    def test_to_float_does_not_raise_for_thousands_separator(self, s):
        """
        Para qualquer string no formato 'X.XXX,XX',
        _to_float(s) NÃO deve lançar ValueError e deve retornar o float correto.
        """
        # Calcula o valor esperado manualmente: remove ponto de milhar, troca vírgula por ponto
        expected = float(s.replace(".", "").replace(",", "."))

        # No código bugado, isso lança ValueError
        result = Entity._to_float(s)

        assert result == pytest.approx(expected), (
            f"_to_float({s!r}) retornou {result}, esperado {expected}"
        )

    def test_to_float_specific_example(self):
        """Exemplo concreto do bug: _to_float('1.234,56') deve retornar 1234.56."""
        result = Entity._to_float("1.234,56")
        assert result == pytest.approx(1234.56), (
            f"_to_float('1.234,56') retornou {result}, esperado 1234.56"
        )


# ---------------------------------------------------------------------------
# Bug A — Purchase._extract com layout multi-linha
# ---------------------------------------------------------------------------

class TestBugA_ExtractMultilineLayout:
    """
    **Validates: Requirements 1.1**

    Bug A: o regex em Purchase não usa re.DOTALL nem aceita \\n entre
    rótulo e valor, então _extract() retorna None quando o PDF extrai
    o texto com quebra de linha entre rótulo e valor.

    Este teste DEVE FALHAR no código não corrigido.
    """

    def test_extract_purchase_total_multiline(self):
        """
        Dado texto com rótulo e valor em linhas separadas,
        _extract deve retornar o valor numérico (não None).
        """
        texto = "Valor Total dos Produtos (R$)\n89,90"
        pattern = r"Valor Total dos Produtos \(R\$\)\s*([\d,.]+)"

        purchase = Purchase()
        result = purchase._extract(texto, pattern)

        assert result == "89,90", (
            f"_extract retornou {result!r}, esperado '89,90'. "
            "Bug A: regex não aceita quebra de linha entre rótulo e valor."
        )

    def test_extract_discount_multiline(self):
        """Setter discount: rótulo e valor em linhas separadas."""
        texto = "Valor Descontos (R$)\n5,00"
        pattern = r"Valor Descontos \(R\$\)\s*([\d,.]+)"

        purchase = Purchase()
        result = purchase._extract(texto, pattern)

        assert result == "5,00", (
            f"_extract retornou {result!r}, esperado '5,00'."
        )

    def test_extract_paid_amount_multiline(self):
        """Setter paid_amount: rótulo e valor em linhas separadas."""
        texto = "Valor Pago (R$)\n89,90"
        pattern = r"Valor Pago \(R\$\)\s*([\d,.]+)"

        purchase = Purchase()
        result = purchase._extract(texto, pattern)

        assert result == "89,90", (
            f"_extract retornou {result!r}, esperado '89,90'."
        )

    def test_purchase_load_multiline_sets_purchase_total(self):
        """
        Quando o texto completo tem rótulo e valor em linhas separadas,
        purchase.purchase_total deve ser 89.9 (não 0.0).
        """
        texto = (
            "Valor Total dos Produtos (R$)\n89,90\n"
            "Valor Descontos (R$)\n0,00\n"
            "Valor Pago (R$)\n89,90\n"
        )
        purchase = Purchase()
        purchase.load(texto)

        assert purchase.purchase_total == pytest.approx(89.9), (
            f"purchase_total={purchase.purchase_total}, esperado 89.9. "
            "Bug A: _extract retornou None → _to_float(None) → 0.0"
        )
