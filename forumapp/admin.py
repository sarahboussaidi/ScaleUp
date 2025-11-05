from django.contrib import admin
from .models import Sujet, Question, Reponse


# ==========================
# INLINE CONFIGURATION
# (permet d'afficher les questions directement dans la page d'un sujet)
# ==========================
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('texte', 'utilisateur', 'date_creation', 'upvotes', 'downvotes')
    readonly_fields = ('date_creation',)


class ReponseInline(admin.TabularInline):
    model = Reponse
    extra = 1
    fields = ('texte', 'utilisateur', 'date_creation', 'upvotes', 'downvotes')
    readonly_fields = ('date_creation',)


# ==========================
# SUJET ADMIN
# ==========================
@admin.register(Sujet)
class SujetAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date_creation', 'upvotes', 'downvotes')
    search_fields = ('titre', 'description')
    list_filter = ('date_creation',)
    inlines = [QuestionInline]
    ordering = ('-date_creation',)


# ==========================
# QUESTION ADMIN
# ==========================
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('texte_court', 'sujet', 'utilisateur', 'date_creation', 'upvotes', 'downvotes')
    search_fields = ('texte', 'sujet__titre', 'utilisateur__username')
    list_filter = ('date_creation',)
    inlines = [ReponseInline]
    ordering = ('-date_creation',)

    def texte_court(self, obj):
        return obj.texte[:50]
    texte_court.short_description = 'Question'


# ==========================
# REPONSE ADMIN
# ==========================
@admin.register(Reponse)
class ReponseAdmin(admin.ModelAdmin):
    list_display = ('texte_court', 'question', 'utilisateur', 'date_creation', 'upvotes', 'downvotes')
    search_fields = ('texte', 'question__texte', 'utilisateur__username')
    list_filter = ('date_creation',)
    ordering = ('-date_creation',)

    def texte_court(self, obj):
        return obj.texte[:50]
    texte_court.short_description = 'Réponse'
