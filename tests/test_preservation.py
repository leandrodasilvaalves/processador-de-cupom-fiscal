"""
Testes de preservação — Property 2: Preservation

Estes testes DEVEM PASSAR no código não corrigido.
Confirmam o comportamento baseline que deve ser preservado após o fix.

Validates: Requirements 3.1, 3.2, 3.3, 3.4
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from entities.entitity import Entity
from entities.purchase import Purchase


# ---------------------------------------------------------------------------
# P2: _to_float sem separador de milhar
# ---------------------------------------------------------------------------

@st.composite
def simple_decimal_format(draw):
    """Gera strings no formato 'X,XX' sem separador de milhar (ex: '89,90')."""
    integer_part = draw(st.integers(min_value=0, max_value=999))
    decimal_part = draw(st.integers(min_value=0, max_value=99))
    return f"{integer_part},{decimal_part:02d}"


class TestPreservation_ToFloat:
    """
    Validates: Requirements 3.2, 3.3

    Garante que _to_float continua funcionando para entradas sem separador de milhar.
    """

    @given(s=simple_decimal_format())
    @settings(max_examples=50)
    def test_to_float_without_thousands_separator(self, s):
        """Para qualquer 'X,XX' sem separador de milhar, _to_float retorna o float correto."""
        expected = float(s.replace(",", "."))
        result = Entity._to_float(s)
        assert result == pytest.approx(expected), (
            f"_to_float({s!r}) retornou {result}, esperado {expected}"
        )

    def test_to_float_none_returns_zero(self):
        """P3: _to_float(None) deve retornar 0.0."""
        assert Entity._to_float(None) == 0.0

    def test_to_float_specific_89_90(self):
        """Exemplo concreto: _to_float('89,90') == 89.9."""
        assert Entity._to_float("89,90") == pytest.approx(89.9)

    def test_to_float_specific_0_50(self):
        """Exemplo concreto: _to_float('0,50') == 0.5."""
        assert Entity._to_float("0,50") == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# P1: Purchase com rótulo e valor na mesma linha (layout padrão)
# ---------------------------------------------------------------------------

class TestPreservation_PurchaseSameLine:
    """
    Validates: Requirements 3.1, 3.4

    Garante que textos com rótulo e valor na mesma linha continuam sendo extraídos.
    """

    def test_purchase_total_same_line(self):
        """Rótulo e valor na mesma linha: purchase_total extraído corretamente."""
        texto = "Valor Total dos Produtos (R$) 89,90"
        purchase = Purchase()
        purchase.load(texto)
        assert purchase.purchase_total == pytest.approx(89.9), (
            f"purchase_total={purchase.purchase_total}, esperado 89.9"
        )

    def test_discount_same_line(self):
        """Rótulo e valor na mesma linha: discount extraído corretamente."""
        texto = "Valor Descontos (R$) 5,00"
        purchase = Purchase()
        purchase.load(texto)
        assert purchase.discount == pytest.approx(5.0), (
            f"discount={purchase.discount}, esperado 5.0"
        )

    def test_paid_amount_same_line(self):
        """Rótulo e valor na mesma linha: paid_amount extraído corretamente."""
        texto = "Valor Pago (R$) 89,90"
        purchase = Purchase()
        purchase.load(texto)
        assert purchase.paid_amount == pytest.approx(89.9), (
            f"paid_amount={purchase.paid_amount}, esperado 89.9"
        )

    def test_full_purchase_same_line(self):
        """Texto completo com layout padrão: todos os campos extraídos corretamente."""
        texto = (
            "Valor Total dos Produtos (R$) 120,50\n"
            "Valor Descontos (R$) 0,00\n"
            "Valor Pago (R$) 120,50\n"
        )
        purchase = Purchase()
        purchase.load(texto)
        assert purchase.purchase_total == pytest.approx(120.5)
        assert purchase.discount == pytest.approx(0.0)
        assert purchase.paid_amount == pytest.approx(120.5)
