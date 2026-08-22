from django import forms

from apps.lojas.models import Loja

from .models import Produto


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            "codigo",
            "nome",
            "categoria",
            "observacao",
            "unidade",
            "estoque_minimo",
            "ativo",
        ]
        widgets = {"observacao": forms.Textarea(attrs={"rows": 2})}


class ImportacaoProdutosForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha XLSX",
        help_text="Cabeçalhos esperados: TIPO, DESCRIÇÃO, TOTAL e OBS.",
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx"}),
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if not arquivo.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("Selecione um arquivo no formato .xlsx.")
        return arquivo


class MovimentacaoForm(forms.Form):
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.none(), empty_label="Selecione um produto"
    )
    quantidade = forms.DecimalField(min_value=0.01, max_digits=12, decimal_places=2)
    documento = forms.CharField(max_length=80, required=False)
    observacao = forms.CharField(
        label="Observação", required=False, widget=forms.Textarea(attrs={"rows": 3})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["produto"].queryset = Produto.objects.filter(ativo=True).order_by("nome")


class SaidaForm(MovimentacaoForm):
    loja = forms.ModelChoiceField(
        queryset=Loja.objects.none(), required=False, empty_label="Sem loja vinculada"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["loja"].queryset = Loja.objects.order_by("codigo")
