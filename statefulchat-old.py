import os
import dotenv
import json
import glob
from openai import OpenAI
from datetime import datetime
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.theme import Theme
    from rich.rule import Rule
    RICH_AVAILABLE = True
    console = Console()
except Exception:
    RICH_AVAILABLE = False
    console = None

dotenv.load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def show_conversation_menu():
    """Muestra el menú de conversaciones disponibles y permite seleccionar una"""
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(logs_dir):
        return None
    
    # Buscar archivos JSON de conversaciones
    json_files = glob.glob(os.path.join(logs_dir, "conversation_*.json"))
    if not json_files:
        return None
    
    # Ordenar por fecha de modificación (más recientes primero)
    json_files.sort(key=os.path.getmtime, reverse=True)
    
    if RICH_AVAILABLE:
        console.print(Panel("Conversaciones disponibles:", title="Historial", border_style="yellow", title_align="left"))
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="bold", width=4)
        table.add_column("Título", style="yellow", width=40)
        table.add_column("Fecha", style="cyan", width=12)
        table.add_column("Hora", style="green", width=8)
        table.add_column("Mensajes", style="white", width=8)
        
        for idx, file_path in enumerate(json_files, 1):
            try:
                filename = os.path.basename(file_path)
                # Extraer fecha y hora del nombre del archivo
                parts = filename.replace("conversation_", "").replace(".json", "").split("_")
                if len(parts) >= 2:
                    date_part = parts[0]
                    time_part = parts[1]
                    
                    # Obtener título y contar mensajes
                    title = get_conversation_title(file_path)
                    with open(file_path, "r", encoding="utf-8") as f:
                        conversation = json.load(f)
                        msg_count = len(conversation)
                    
                    table.add_row(str(idx), title, date_part, time_part, str(msg_count))
            except Exception:
                continue
        
        console.print(table)
        console.print("\n[bold]Opciones:[/]")
        console.print("[green]• Número (1-{})[/] - Cargar conversación".format(len(json_files)))
        console.print("[blue]• 'nuevo' o 'n'[/] - Iniciar nueva conversación")
        console.print("[red]• 'borrar' o 'b'[/] - Eliminar conversación")
        console.print("[red]• 'salir' o 's'[/] - Salir del programa")
        
        while True:
            choice = console.input("\n[bold yellow]Selecciona una opción:[/] ").strip().lower()
            
            if choice in ['salir', 's']:
                return "exit"
            elif choice in ['nuevo', 'n']:
                return None
            elif choice in ['borrar', 'b']:
                return "delete"
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(json_files):
                    return json_files[idx]
                else:
                    console.print("[red]Número inválido. Intenta de nuevo.[/]")
            else:
                console.print("[red]Opción inválida. Intenta de nuevo.[/]")
    else:
        print("\nConversaciones disponibles:")
        for idx, file_path in enumerate(json_files, 1):
            try:
                filename = os.path.basename(file_path)
                parts = filename.replace("conversation_", "").replace(".json", "").split("_")
                if len(parts) >= 2:
                    date_part = parts[0]
                    time_part = parts[1]
                    title = get_conversation_title(file_path)
                    with open(file_path, "r", encoding="utf-8") as f:
                        conversation = json.load(f)
                        msg_count = len(conversation)
                    print(f"{idx}. [{title}] {date_part} {time_part} ({msg_count} mensajes)")
            except Exception:
                continue
        
        print("\nOpciones:")
        print("• Número (1-{}) - Cargar conversación".format(len(json_files)))
        print("• 'nuevo' o 'n' - Iniciar nueva conversación")
        print("• 'borrar' o 'b' - Eliminar conversación")
        print("• 'salir' o 's' - Salir del programa")
        
        while True:
            choice = input("\nSelecciona una opción: ").strip().lower()
            
            if choice in ['salir', 's']:
                return "exit"
            elif choice in ['nuevo', 'n']:
                return None
            elif choice in ['borrar', 'b']:
                return "delete"
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(json_files):
                    return json_files[idx]
                else:
                    print("Número inválido. Intenta de nuevo.")
            else:
                print("Opción inválida. Intenta de nuevo.")

def load_conversation(file_path):
    """Carga una conversación desde un archivo JSON"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]Error al cargar conversación: {e}[/]")
        else:
            print(f"Error al cargar conversación: {e}")
        return None

def generate_conversation_title(conversation):
    """Genera un título para la conversación basado en el primer mensaje del usuario"""
    for msg in conversation:
        if msg.get("role") == "user":
            user_message = msg.get("content", "")
            # Crear título truncando el primer mensaje (máximo 50 caracteres)
            if len(user_message) > 50:
                title = user_message[:47] + "..."
            else:
                title = user_message
            return title
    return "Conversación sin título"

def get_conversation_title(file_path):
    """Obtiene el título de una conversación desde el archivo JSON"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            conversation = json.load(f)
            # Buscar título guardado o generar uno
            for msg in conversation:
                if msg.get("role") == "system" and "title" in msg:
                    return msg["title"]
            return generate_conversation_title(conversation)
    except Exception:
        return "Error al cargar título"

def delete_conversation():
    """Permite al usuario seleccionar y eliminar una conversación"""
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(logs_dir):
        if RICH_AVAILABLE:
            console.print("[red]No hay conversaciones para eliminar.[/]")
        else:
            print("No hay conversaciones para eliminar.")
        return
    
    # Buscar archivos JSON de conversaciones
    json_files = glob.glob(os.path.join(logs_dir, "conversation_*.json"))
    if not json_files:
        if RICH_AVAILABLE:
            console.print("[red]No hay conversaciones para eliminar.[/]")
        else:
            print("No hay conversaciones para eliminar.")
        return
    
    # Ordenar por fecha de modificación (más recientes primero)
    json_files.sort(key=os.path.getmtime, reverse=True)
    
    if RICH_AVAILABLE:
        console.print(Panel("Selecciona la conversación a eliminar:", title="Eliminar", border_style="red", title_align="left"))
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="bold", width=4)
        table.add_column("Título", style="yellow", width=40)
        table.add_column("Fecha", style="cyan", width=12)
        table.add_column("Hora", style="green", width=8)
        
        for idx, file_path in enumerate(json_files, 1):
            try:
                filename = os.path.basename(file_path)
                parts = filename.replace("conversation_", "").replace(".json", "").split("_")
                if len(parts) >= 2:
                    date_part = parts[0]
                    time_part = parts[1]
                    title = get_conversation_title(file_path)
                    table.add_row(str(idx), title, date_part, time_part)
            except Exception:
                continue
        
        console.print(table)
        console.print("\n[bold red]Opciones:[/]")
        console.print("[green]• Número (1-{})[/] - Eliminar conversación".format(len(json_files)))
        console.print("[blue]• 'cancelar' o 'c'[/] - Volver al menú principal")
        
        while True:
            choice = console.input("\n[bold red]Selecciona conversación a eliminar:[/] ").strip().lower()
            
            if choice in ['cancelar', 'c']:
                return
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(json_files):
                    file_to_delete = json_files[idx]
                    title = get_conversation_title(file_to_delete)
                    
                    # Confirmar eliminación
                    confirm = console.input(f"[bold red]¿Eliminar '{title}'? (sí/no):[/] ").strip().lower()
                    if confirm in ['sí', 'si', 's', 'yes', 'y']:
                        try:
                            # Eliminar archivos JSON y log asociados
                            base_filename = os.path.basename(file_to_delete).replace("conversation_", "").replace(".json", "")
                            log_file = os.path.join(logs_dir, f"log_{base_filename}.txt")
                            
                            os.remove(file_to_delete)
                            if os.path.exists(log_file):
                                os.remove(log_file)
                            
                            console.print(f"[green]Conversación '{title}' eliminada correctamente.[/]")
                        except Exception as e:
                            console.print(f"[red]Error al eliminar: {e}[/]")
                    else:
                        console.print("[yellow]Eliminación cancelada.[/]")
                    return
                else:
                    console.print("[red]Número inválido. Intenta de nuevo.[/]")
            else:
                console.print("[red]Opción inválida. Intenta de nuevo.[/]")
    else:
        print("\nSelecciona la conversación a eliminar:")
        for idx, file_path in enumerate(json_files, 1):
            try:
                filename = os.path.basename(file_path)
                parts = filename.replace("conversation_", "").replace(".json", "").split("_")
                if len(parts) >= 2:
                    date_part = parts[0]
                    time_part = parts[1]
                    title = get_conversation_title(file_path)
                    print(f"{idx}. [{title}] {date_part} {time_part}")
            except Exception:
                continue
        
        print("\nOpciones:")
        print("• Número (1-{}) - Eliminar conversación".format(len(json_files)))
        print("• 'cancelar' o 'c' - Volver al menú principal")
        
        while True:
            choice = input("\nSelecciona conversación a eliminar: ").strip().lower()
            
            if choice in ['cancelar', 'c']:
                return
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(json_files):
                    file_to_delete = json_files[idx]
                    title = get_conversation_title(file_to_delete)
                    
                    # Confirmar eliminación
                    confirm = input(f"¿Eliminar '{title}'? (sí/no): ").strip().lower()
                    if confirm in ['sí', 'si', 's', 'yes', 'y']:
                        try:
                            # Eliminar archivos JSON y log asociados
                            base_filename = os.path.basename(file_to_delete).replace("conversation_", "").replace(".json", "")
                            log_file = os.path.join(logs_dir, f"log_{base_filename}.txt")
                            
                            os.remove(file_to_delete)
                            if os.path.exists(log_file):
                                os.remove(log_file)
                            
                            print(f"Conversación '{title}' eliminada correctamente.")
                        except Exception as e:
                            print(f"Error al eliminar: {e}")
                    else:
                        print("Eliminación cancelada.")
                    return
                else:
                    print("Número inválido. Intenta de nuevo.")
            else:
                print("Opción inválida. Intenta de nuevo.")

def main():
    while True:
        # Mostrar menú de conversaciones
        selected_conversation = show_conversation_menu()
        
        if selected_conversation == "exit":
            if RICH_AVAILABLE:
                console.print(Panel("¡Hasta pronto!", border_style="cyan", title="Salir", title_align="left"))
            else:
                print("¡Hasta pronto!")
            return
        elif selected_conversation == "delete":
            delete_conversation()
            continue  # Volver al menú principal
        
        # Cargar conversación seleccionada o crear nueva
        if selected_conversation:
            conversation = load_conversation(selected_conversation)
            if conversation is None:
                continue  # Volver al menú si hay error
            if RICH_AVAILABLE:
                console.print(Panel(f"Conversación cargada: {os.path.basename(selected_conversation)}", title="Cargado", border_style="green", title_align="left"))
            else:
                print(f"Conversación cargada: {os.path.basename(selected_conversation)}")
        else:
            conversation = [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente útil y profesional. Responde en español con tono formal y cercano. "
                        "Puedes usar emoticonos con moderación para dar calidez o enfatizar (por ejemplo: 😊, 💡, ✅, ⚠️, 📌), "
                        "sin exceder 1–2 por respuesta y evitando informalidad excesiva."
                    ),
                }
            ]
            if RICH_AVAILABLE:
                console.print(Panel("Nueva conversación iniciada", title="Nuevo", border_style="cyan", title_align="left"))
            else:
                print("Nueva conversación iniciada")
        
        if RICH_AVAILABLE:
            console.print(Panel("Comandos disponibles:\n• 'Contexto' - Ver historial\n• 'Salir' - Finalizar", title="Ayuda", border_style="blue", title_align="left"))
        else:
            print("Comandos: 'Contexto' para ver historial, 'Salir' para finalizar")
        
        model = "gpt-4o-mini"

        # Configuración de logs: crear carpeta y archivo con nombre log_dia_hora.txt
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Determinar si es una conversación nueva o una continuación
        if selected_conversation:
            # Continuar conversación existente - usar el mismo archivo
            base_filename = os.path.basename(selected_conversation).replace("conversation_", "").replace(".json", "")
            log_file_path = os.path.join(logs_dir, f"log_{base_filename}.txt")
            json_file_path = selected_conversation
        else:
            # Nueva conversación - crear nuevos archivos
            now = datetime.now()
            dia = now.strftime("%Y-%m-%d")
            hora = now.strftime("%H-%M-%S")
            log_file_path = os.path.join(logs_dir, f"log_{dia}_{hora}.txt")
            json_file_path = os.path.join(logs_dir, f"conversation_{dia}_{hora}.json")

        def write_log(line: str) -> None:
            try:
                with open(log_file_path, "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {line}\n")
            except Exception:
                # Evitar que errores de logging rompan la conversación
                pass

        def save_conversation_json() -> None:
            """Guarda la variable conversation en un archivo JSON"""
            try:
                with open(json_file_path, "w", encoding="utf-8") as f:
                    json.dump(conversation, f, ensure_ascii=False, indent=2)
            except Exception:
                # Evitar que errores de JSON rompan la conversación
                pass

        if selected_conversation:
            write_log("=== Continuación de conversación ===")
        else:
            write_log("=== Inicio de conversación ===")
            write_log(f"Sistema: {conversation[0]['content']}")
        
        while True:
            if RICH_AVAILABLE:
                console.print(Rule(style="grey50"))
                user_input = console.input("[bold blue]Usuario >[/] ")
            else:
                user_input = input("You: ")
            
            if user_input.strip().lower() == "salir":
                if RICH_AVAILABLE:
                    console.print(Panel("¡Hasta pronto!", border_style="cyan", title="Salir", title_align="left"))
                else:
                    print("¡Hasta pronto!")
                write_log("=== Fin de conversación por comando 'Salir' ===")
                save_conversation_json()  # Guardar conversación final en JSON
                break
            
            # Comando especial "Contexto": muestra todo el historial de la conversación
            # (roles y contenidos) sin realizar una llamada al modelo, y continúa el bucle.
            if user_input.strip().lower() == "contexto":
                write_log("[Comando] Contexto solicitado")
                save_conversation_json()  # Guardar contexto actual en JSON
                if RICH_AVAILABLE:
                    table = Table(title="Contexto actual", show_lines=True)
                    table.add_column("#", style="bold", width=4)
                    table.add_column("Rol", style="magenta", no_wrap=True)
                    table.add_column("Contenido", style="white")
                    for idx, msg in enumerate(conversation, start=1):
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        role_style = "cyan" if role == "system" else ("green" if role == "assistant" else "yellow")
                        role_es = "Sistema" if role == "system" else ("Agente" if role == "assistant" else ("Usuario" if role == "user" else role))
                        table.add_row(str(idx), f"[{role_style}]{role_es}[/{role_style}]", content)
                    console.print(table)
                else:
                    print("Contexto actual:")
                    for idx, msg in enumerate(conversation, start=1):
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        role_es = "Sistema" if role == "system" else ("Agente" if role == "assistant" else ("Usuario" if role == "user" else role))
                        print(f"{idx}. {role_es}: {content}")
                continue
            
            if RICH_AVAILABLE:
                console.print(Panel(user_input, title="Usuario", title_align="left", border_style="blue"))
            write_log(f"Usuario: {user_input}")
            conversation.append({"role": "user", "content": user_input})
            
            # Si es el primer mensaje del usuario, generar y guardar título
            if len([msg for msg in conversation if msg.get("role") == "user"]) == 1:
                title = generate_conversation_title(conversation)
                # Agregar título al mensaje del sistema
                if conversation[0].get("role") == "system":
                    conversation[0]["title"] = title
            
            try:
                if RICH_AVAILABLE:
                    with console.status("[bold green]El agente está pensando…[/]", spinner="dots"):
                        response = client.chat.completions.create(
                            model=model,
                            messages=conversation
                        )
                else:
                    print("El agente está pensando…")
                    response = client.chat.completions.create(
                        model=model,
                        messages=conversation
                    )
                text = response.choices[0].message.content.strip()
                if RICH_AVAILABLE:
                    console.print(Panel(text, title="Agente", title_align="left", border_style="green"))
                else:
                    print(f"Bot: {text}")
                conversation.append({"role": "assistant", "content": text})
                write_log(f"Agente: {text}")
                save_conversation_json()  # Guardar conversación actualizada en JSON
            except Exception as e:
                if RICH_AVAILABLE:
                    console.print(f"Error: {e}", style="bold red")
                else:
                    print(f"Error: {e}")
                write_log(f"Error: {e}")

if __name__ == "__main__":
    main()