from django import forms

from .models import Loja


class LojaForm(forms.ModelForm):
    class Meta:
        model = Loja
        fields = ["codigo", "nome", "lane"]


class ImportacaoLojasForm(forms.Form):
    arquivo = forms.FileField(
        label="Cronograma em PDF",
        help_text="Selecione o PDF do cronograma contendo as colunas Lane e Loja.",
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,application/pdf"}),
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if not arquivo.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Selecione um arquivo no formato PDF.")
        return arquivo
