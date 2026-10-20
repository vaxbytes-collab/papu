import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COG_FILES = (
    "seguridad.py",
    "moderacion.py",
    "utilidades.py",
    "entretenimiento.py",
    "juegos.py",
)
DISCORD_GLOBAL_CHAT_INPUT_COMMAND_LIMIT = 100


def declared_group_commands():
    commands = []
    for filename in COG_FILES:
        tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"), filename=filename)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                if decorator.func.attr != "command":
                    continue
                owner = decorator.func.value
                if not isinstance(owner, ast.Name) or owner.id not in {"guardia", "arcade"}:
                    continue
                name = next(
                    (
                        keyword.value.value
                        for keyword in decorator.keywords
                        if keyword.arg == "name"
                        and isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)
                    ),
                    node.name,
                )
                commands.append((name, filename))
    return commands


def declared_slash_commands():
    commands = []
    for filename in COG_FILES:
        tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"), filename=filename)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                if decorator.func.attr != "command":
                    continue
                owner = decorator.func.value
                if not isinstance(owner, ast.Name) or owner.id != "app_commands":
                    continue
                name = next(
                    (
                        keyword.value.value
                        for keyword in decorator.keywords
                        if keyword.arg == "name"
                        and isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)
                    ),
                    node.name,
                )
                commands.append((name, filename))
    return commands


class CommandRegistryTests(unittest.TestCase):
    def test_slash_command_names_are_unique(self):
        commands = declared_slash_commands()
        names = [name for name, _ in commands]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        self.assertEqual(duplicates, [], f"Slash command names must be unique: {duplicates}")

    def test_slash_command_count_stays_within_discord_limit(self):
        commands = declared_slash_commands()
        self.assertLessEqual(
            len(commands),
            DISCORD_GLOBAL_CHAT_INPUT_COMMAND_LIMIT,
            f"Found {len(commands)} slash commands; consolidate commands into groups before exceeding the platform limit.",
        )

    def test_music_and_redundant_commands_are_removed(self):
        names = {name for name, _ in declared_slash_commands()}
        names.update(name for name, _ in declared_group_commands())
        removed = {
            "play", "cola", "pause", "resume", "skip", "stop",
            "bola8_clasica", "dado_clasico", "moneda_clasica", "ppt_clasico",
            "caos", "ruleta", "fortuna", "nombre_banda", "nombre_usuario",
            "pov", "superpoder", "villano", "mood_michi", "verso_michi",
            "npc", "excusa_gamer", "cancion_inventada", "lore_aleatorio",
            "traductor_michi", "animal_aleatorio", "objeto_legendario",
            "mision_secundaria", "rango_gamer", "jefe_final",
        }
        self.assertTrue(removed.isdisjoint(names), f"Commands slated for removal remain: {sorted(removed & names)}")
        self.assertFalse((ROOT / "musica.py").exists(), "The voice-music module should be deleted")
        self.assertNotIn('"musica"', (ROOT / "main.py").read_text(encoding="utf-8"))
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertNotIn("yt-dlp", requirements)
        self.assertNotIn("PyNaCl", requirements)

    def test_moderation_message_handler_is_defined_once(self):
        tree = ast.parse((ROOT / "moderacion.py").read_text(encoding="utf-8"))
        cog = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Moderacion")
        handlers = [node for node in cog.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "check_message"]
        self.assertEqual(len(handlers), 1, "Duplicate check_message methods silently shadow one another")

    def test_megaupdate_commands_are_present(self):
        names = {name for name, _ in declared_slash_commands()}
        expected = {
            "antispam", "antiraid", "antienlaces", "antimenciones",
            "antirepeticion", "filtro_caps", "palabra_bloquear",
            "palabra_permitir", "palabras_bloqueadas", "canal_reportes",
            "reportar", "auditoria_permisos", "purge_usuario", "purge_bots",
            "apodo", "rol_dar", "rol_quitar", "timeout_estado",
            "adivinanza", "dado_personalizado", "dato_michi", "reto_sano",
            "palabra_aleatoria", "duelo", "completa_frase",
        }
        names.update(name for name, _ in declared_group_commands())
        self.assertTrue(expected.issubset(names), f"Missing commands: {sorted(expected - names)}")


if __name__ == "__main__":
    unittest.main()
