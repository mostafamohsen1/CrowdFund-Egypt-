from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Project, Category, Donation, Comment, Rating, Report


class ProjectForm(forms.ModelForm):
    tag_names = forms.CharField(
        label=_("Tags"),
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. tech, education, charity, cairo (comma separated)',
            'class': 'form-control'
        }),
        help_text=_("Enter comma-separated tags to help supporters discover your campaign.")
    )

    class Meta:
        model = Project
        fields = ['title', 'category', 'details', 'total_target', 'start_time', 'end_time', 'cover_image']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Campaign Title', 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'details': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe your campaign goals, impact, and usage of funds...', 'class': 'form-control'}),
            'total_target': forms.NumberInput(attrs={'placeholder': '250000', 'step': '0.01', 'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if end_time <= start_time:
                self.add_error('end_time', _("Campaign end date must be after the start date."))
        return cleaned_data


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'class': 'form-control'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ProjectGalleryImagesForm(forms.Form):
    images = MultipleFileField(
        label=_("Additional Gallery Pictures"),
        required=False,
        help_text=_("Upload up to 5 additional project showcase photos.")
    )


class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'placeholder': 'Enter amount in EGP (e.g. 100)',
                'min': '1',
                'step': '1',
                'class': 'form-control form-control-lg'
            })
        }


class CommentForm(forms.ModelForm):
    parent_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Write a comment or encouraging message...',
                'class': 'form-control'
            })
        }


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f"{i} Stars") for i in range(1, 6)])
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Please specify why this project or comment is inappropriate...',
                'class': 'form-control'
            })
        }
