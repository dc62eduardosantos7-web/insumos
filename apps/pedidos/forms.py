from django import forms
from django.forms import BaseFormSet, formset_factory

from apps.estoque.models import Produto
from apps.lojas.models import Loja
from apps.usuarios.models import PerfilUsuario
from apps.usuarios.permissoes import obter_papel


class PedidoForm(forms.Form):
    loja = forms.ModelChoiceField(
        queryset=Loja.objects.none(), empty_label="Selecione uma loja"
    )
    data = forms.DateField(
        label="Data da solicitação",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    observacoes = forms.CharField(
        label="Observações gerais",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        papel = obter_papel(usuario)
        if papel == PerfilUsuario.LOJA:
            self.fields.pop("loja")
        else:
            self.fields["loja"].queryset = Loja.objects.order_by("codigo")


class ItemPedidoForm(forms.Form):
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.none(), empty_label="Selecione um produto"
    )
    quantidade = forms.DecimalField(
        label="Quantidade", min_value=0.01, max_digits=12, decimal_places=2
    )
    observacao = forms.CharField(label="Observação", required=False, max_length=255)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["produto"].queryset = Produto.objects.filter(ativo=True).order_by(
            "nome"
        )


class BaseItensPedidoFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        preenchidos = [
            form
            for form in self.forms
            if form.cleaned_data and form.cleaned_data.get("produto")
        ]
        if not preenchidos:
            raise forms.ValidationError("Adicione pelo menos um produto ao pedido.")
        produtos = [form.cleaned_data["produto"].pk for form in preenchidos]
        if len(produtos) != len(set(produtos)):
            raise forms.ValidationError("O mesmo produto não pode aparecer duas vezes.")


ItensPedidoFormSet = formset_factory(
    ItemPedidoForm,
    formset=BaseItensPedidoFormSet,
    extra=1,
)


class QuantidadesPedidoForm(forms.Form):
    justificativa = forms.CharField(
        label="Justificativa da alteração",
        required=True,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(
        self,
        *args,
        itens,
        modo="solicitada",
        justificativa_obrigatoria=True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.fields["justificativa"].required = justificativa_obrigatoria
        if modo == "separada":
            self.fields["justificativa"].label = "Observação da separação"
        self.itens = list(itens)
        for item in self.itens:
            if modo == "aprovada":
                inicial = item.quantidade_aprovada or item.quantidade
                rotulo = "Quantidade aprovada"
                minimo = 0.01
            elif modo == "separada":
                inicial = item.quantidade_liberada
                rotulo = "Quantidade separada"
                minimo = 0
            else:
                inicial = item.quantidade
                rotulo = "Quantidade solicitada"
                minimo = 0.01
            self.fields[f"item_{item.pk}"] = forms.DecimalField(
                label=f"{item.produto.codigo} · {item.produto.nome} — {rotulo}",
                min_value=minimo,
                max_digits=12,
                decimal_places=2,
                initial=inicial,
            )

    @property
    def quantidades(self):
        return {
            item.pk: self.cleaned_data[f"item_{item.pk}"] for item in self.itens
        }


class JustificativaForm(forms.Form):
    justificativa = forms.CharField(
        label="Justificativa",
        required=True,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class ObservacaoForm(forms.Form):
    observacao = forms.CharField(
        label="Observação",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

