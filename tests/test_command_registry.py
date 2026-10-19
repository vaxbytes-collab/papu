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
    "musica.py",
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

    def test_megaupdate_commands_are_present(self):
        names = {name for name, _ in declared_slash_commands()}
        expected = {
            "antispam",
            "antiraid",
            "antienlaces",
            "antimenciones",
            "antirepeticion",
            "filtro_caps",
            "palabra_bloquear",
            "palabra_permitir",
            "palabras_bloqueadas",
            "canal_reportes",
            "reportar",
            "auditoria_permisos",
            "purge_usuario",
            "purge_bots",
            "apodo",
            "rol_dar",
            "rol_quitar",
            "timeout_estado",
            "adivinanza",
            "dado_personalizado",
            "fortuna",
            "nombre_banda",
            "nombre_usuario",
            "pov",
            "superpoder",
            "villano",
            "dato_michi",
            "reto_sano",
            "mood_michi",
            "palabra_aleatoria",
            "duelo_aleatorio",
            "completa_frase",
            "verso_michi",
            "npc",
            "excusa_gamer",
            "cancion_inventada",
            "lore_aleatorio",
            "traductor_michi",
        }
        names.update(name for name, _ in declared_group_commands())
        self.assertTrue(expected.issubset(names), f"Missing commands: {sorted(expected - names)}")


if __name__ == "__main__":
    unittest.main()
