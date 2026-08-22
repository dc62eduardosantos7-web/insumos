from django import forms


class ImportacaoLoginsLojasForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha de credenciais",
        help_text="Selecione a planilha Logins_Lojas_FY27.xlsx.",
        widget=forms.ClearableFileInput(
            attrs={
                "accept": ".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        ),
    )
    redefinir_senhas = forms.BooleanField(
        label="Redefinir também as senhas de usuários já existentes",
        required=False,
        help_text="Deixe desmarcado para preservar os acessos que já estão em uso.",
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if not arquivo.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("Selecione um arquivo no formato XLSX.")
        if arquivo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("O arquivo deve ter no máximo 5 MB.")
        return arquivo
