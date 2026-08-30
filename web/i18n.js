(() => {
  const queryLanguage = new URLSearchParams(location.search).get("lang");
  if (["en", "es"].includes(queryLanguage)) localStorage.setItem("peti.language", queryLanguage);

  const translations = new Map(Object.entries({
    "Biblioteca": "Library", "Plan": "Plan", "Compartir": "Share", "Ayuda": "Help",
    "Ajustes": "Settings", "Admin": "Admin", "Salir": "Sign out", "Inicio": "Home",
    "Analizar": "Analyze", "Historial": "History", "Perfil": "Profile", "Agentes": "Agents",
    "Demo PETi": "PETi demo", "Selecciona una mascota para probar sus evidencias.": "Select a pet to explore its evidence.",
    "2 mascotas": "2 pets", "Golden retriever · Sana": "Golden retriever · Healthy",
    "Border collie · Observación": "Border collie · Needs observation",
    "Resumen diario": "Daily overview", "Todo lo importante, hoy.": "Everything important, today.",
    "Información clara para cuidar mejor a tu mascota.": "Clear information to care for your pet.",
    "Tu mascota": "Your pet", "Perfil pendiente": "Profile pending", "Perfil registrado": "Profile saved",
    "Añade tu primera mascota": "Add your first pet", "Activo": "Active", "Sin datos": "No data",
    "Salud general": "General health", "Actividad": "Activity", "Cuidados": "Care",
    "Mejor siguiente paso": "Best next step", "Registra una observación o analiza una evidencia para construir un resumen basado en datos reales.": "Record an observation or analyze evidence to build a summary based on real data.",
    "Analizar ahora": "Analyze now", "Ver historial": "View history", "Estado": "Status",
    "Información honesta": "Honest information", "Las métricas aparecen cuando existen observaciones guardadas.": "Metrics appear only when saved observations exist.",
    "Revisión de evidencia": "Evidence review", "Analiza una nueva observación": "Analyze a new observation",
    "Sube una imagen, audio, vídeo o documento. PETi separa hechos observables de inferencias.": "Upload an image, audio, video or document. PETi separates observable facts from inferences.",
    "Foto": "Photo", "Vídeo": "Video", "Audio": "Audio", "Documento": "Document",
    "Evidencia seleccionada": "Selected evidence", "Iniciar análisis": "Start analysis", "Cancelar": "Cancel",
    "Sin evidencia seleccionada": "No evidence selected", "Selecciona una fuente antes de iniciar el análisis.": "Select a source before starting the analysis.",
    "Historial basado en fuentes": "Source-based history", "Observaciones y resultados": "Observations and results",
    "Cada elemento conserva su origen y nivel de certeza.": "Every item preserves its source and confidence level.",
    "Todo": "All", "Imágenes": "Images", "Audios": "Audio", "Vídeos": "Videos", "Documentos": "Documents",
    "Sin eventos todavía": "No events yet", "Las observaciones guardadas aparecerán aquí con su procedencia.": "Saved observations will appear here with their provenance.",
    "Tu mascota, organizada.": "Your pet, organized.", "Edita los datos básicos y conserva el control de tu información.": "Edit basic details and keep control of your information.",
    "Perfil de mascota": "Pet profile", "Nombre": "Name", "Especie": "Species", "Guardar cambios": "Save changes",
    "Eliminar": "Delete", "Privacidad": "Privacy", "Tus datos se consultan dentro de tu cuenta y las fuentes permanecen visibles.": "Your data remains inside your account and sources stay visible.",
    "Exportar mis datos": "Export my data", "Eliminar cuenta": "Delete account",
    "Workspace": "Workspace", "PETi coordina una revisión.": "PETi coordinates a review.",
    "Cada agente conserva estado, evidencia y revisión de seguridad.": "Each agent preserves state, evidence and safety review.",
    "Sin diagnóstico ni prescripción. Las conclusiones requieren evidencia y límites explícitos.": "No diagnosis or prescription. Conclusions require evidence and explicit limits.",
    "Flujo multi-agente": "Multi-agent workflow", "Coordinador PETi": "PETi coordinator",
    "Recibe el objetivo y distribuye el trabajo.": "Receives the goal and delegates work.",
    "Agente de evidencia": "Evidence agent", "Busca y organiza fuentes guardadas.": "Finds and organizes saved sources.",
    "Especialista": "Specialist", "Interpreta solo la capacidad solicitada.": "Interprets only the requested capability.",
    "Agente de seguridad": "Safety agent", "Revisa incertidumbre y señales de alerta.": "Reviews uncertainty and warning signals.",
    "Iniciar revisión": "Start review", "Revisión en curso": "Review in progress", "· Estado:": "· Status:",
    "Vista previa interactiva: simula los estados del flujo y no crea una ejecución en el backend. Inicia sesión con una cuenta de revisión para ejecutar el flujo real de Cloud Run y ADK.": "Interactive preview: it simulates workflow states and does not create a backend run. Sign in with a reviewer account to execute the real Cloud Run and ADK workflow.",
    "Administración": "Administration", "Estado operativo": "Operational status",
    "Métricas técnicas protegidas para operadores autorizados.": "Technical metrics protected for authorized operators.",
    "Comprobando permisos…": "Checking permissions…", "No se muestran datos operativos hasta validar el rol.": "Operational data is hidden until the role is validated.",
    "Busca en la historia de tu mascota": "Search your pet's history", "Encuentra datos guardados y conserva siempre su procedencia.": "Find saved data while preserving provenance.",
    "Buscar": "Search", "Buscar en mis fuentes": "Search my sources", "Biblioteca basada en fuentes": "Source-based library",
    "Las respuestas y resultados se limitan a la información guardada en tu cuenta.": "Answers and results are limited to information saved in your account.",
    "Colaboración": "Collaboration", "Comparte el cuidado": "Share care", "Invita a una persona concreta con permisos limitados y caducidad opcional.": "Invite a specific person with limited permissions and optional expiry.",
    "Usuario invitado": "Invited user", "Rol": "Role", "Cuidador": "Caregiver", "Solo lectura": "Read only",
    "Duración (horas)": "Duration (hours)", "Opcional": "Optional", "Enviar invitación": "Send invitation",
    "Feedback y soporte": "Feedback and support", "Cuéntanos qué ha ocurrido y te responderemos con contexto seguro.": "Tell us what happened and we will respond with safe context.",
    "Tipo": "Type", "Sugerencia": "Suggestion", "Problema técnico": "Technical issue", "Seguridad": "Safety",
    "Mensaje": "Message", "Enviar feedback": "Send feedback", "Plan PETi": "PETi plan", "Tu plan y tus límites": "Your plan and limits",
    "Consulta tu acceso sin confundir suscripción con seguridad clínica.": "Review access without confusing subscription with clinical safety.",
    "Plan gratuito": "Free plan", "Estado pendiente": "Status pending", "El estado lo determina el backend.": "The backend determines this status.",
    "Los resultados existentes y las funciones de seguridad no dependen de una suscripción.": "Existing results and safety features do not depend on a subscription.",
    "Gestionar preferencias": "Manage preferences", "Preferencias": "Preferences", "Adapta PETi a tu forma de cuidar.": "Adapt PETi to the way you care.",
    "Idioma": "Language", "Tema": "Theme", "Español": "Spanish", "Claro": "Light", "Oscuro": "Dark", "Guardar preferencias": "Save preferences",
    "Calendario y Body Check": "Calendar and Body Check", "Organiza rutinas y revisiones sin convertirlas en diagnóstico.": "Organize routines and checks without turning them into a diagnosis.",
    "Próximos cuidados": "Upcoming care", "Sin eventos registrados": "No events recorded", "Añade una medicación, paseo, vacuna o cita veterinaria para verla aquí.": "Add medication, a walk, vaccination or veterinary visit to see it here.",
    "Medicación": "Medication", "Paseo": "Walk", "Vacuna": "Vaccination", "Cita veterinaria": "Veterinary visit",
    "Descripción": "Description", "Fecha y hora": "Date and time", "Añadir evento": "Add event", "Iniciar Body Check": "Start Body Check",
    "No es un diagnóstico. Las revisiones muestran señales observables y siempre indican cuándo consultar al veterinario.": "This is not a diagnosis. Reviews show observable signs and indicate when to contact a veterinarian.",
    "Documentos y registros": "Documents and records", "Conserva fuentes visibles y revisa los hechos antes de guardarlos.": "Keep sources visible and review facts before saving.",
    "Subir documento": "Upload document", "No hay documentos todavía": "No documents yet", "Los informes veterinarios y sus hechos extraídos aparecerán aquí con su origen.": "Veterinary reports and extracted facts will appear here with their source.",
    "Asistente PETi": "PETi assistant", "Pregunta sobre tu historial": "Ask about your history", "Respuestas basadas en las fuentes guardadas de tu mascota.": "Answers based on your pet's saved sources.",
    "Asistente grounded": "Grounded assistant", "Solo responderá con información relevante de tus registros y mostrará sus fuentes.": "It only answers from relevant saved records and shows its sources.",
    "Pregunta": "Question", "Consultar fuentes": "Consult sources", "Revisión visible de bienestar": "Visible wellbeing review",
    "Marca únicamente lo que observes. PETi no diagnostica ni estima enfermedades.": "Mark only what you observe. PETi does not diagnose or estimate disease.",
    "Revisión pendiente": "Review pending", "Completa las observaciones con buena luz y detente si tu mascota se incomoda.": "Complete observations in good light and stop if your pet becomes uncomfortable.",
    "Ojos": "Eyes", "Oídos": "Ears", "Piel y pelaje": "Skin and coat", "Patas y postura": "Legs and posture",
    "Respiración en reposo": "Breathing at rest", "Heces observables": "Observable stool", "Sin señales visibles preocupantes": "No concerning visible signs",
    "Finalizar revisión": "Finish review", "Si detectas dolor, dificultad respiratoria, sangrado o un cambio intenso, contacta con un veterinario.": "If you observe pain, breathing difficulty, bleeding or a severe change, contact a veterinarian."
    ,"DOG · Perfil registrado": "DOG · Profile saved",
    "Analizar y entender": "Analyze and understand", "Elige una evidencia. PETi observa señales visibles y declara sus límites.": "Choose evidence. PETi observes visible signs and states its limits.",
    "¿Qué quieres observar?": "What do you want to observe?", "Cada análisis conserva su origen y requiere evidencia suficiente.": "Every analysis preserves its source and requires sufficient evidence.",
    "Detalles visibles": "Visible details", "Movimiento y postura": "Movement and posture", "Sonidos del entorno": "Environmental sounds", "Informe veterinario": "Veterinary report",
    "No es un diagnóstico.": "This is not a diagnosis.", "Si la evidencia es insuficiente o hay señales preocupantes, consulta a un veterinario.": "If evidence is insufficient or signs are concerning, contact a veterinarian.",
    "Todo en orden y con origen claro.": "Everything organized with clear provenance.", "Consulta registros, mediciones y análisis guardados.": "Review saved records, measurements and analyses.",
    "Análisis": "Analyses", "Mediciones": "Measurements", "Sin registros todavía": "No records yet",
    "Acceso restringido": "Restricted access", "Inicia sesión con una cuenta autorizada.": "Sign in with an authorized account."
  }));

  const patterns = [
    [/^Evidencias de (.+):$/, "Evidence for $1:"],
    [/^Evidencia (\d+) de (.+)$/, "Evidence $1 for $2"],
    [/^Seleccionar (.+)$/, "Select $1"]
  ];

  function translated(value) {
    const direct = translations.get(value);
    if (direct) return direct;
    for (const [pattern, replacement] of patterns) if (pattern.test(value)) return value.replace(pattern, replacement);
    return value;
  }

  function apply(root = document.body) {
    if (document.documentElement.lang !== "en" || !root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const value = node.nodeValue;
      const trimmed = value.trim();
      if (!trimmed) continue;
      const next = translated(trimmed);
      if (next !== trimmed) node.nodeValue = value.replace(trimmed, next);
    }
    const elements = root.querySelectorAll?.("[placeholder], [title], [aria-label], [alt]") || [];
    for (const element of elements) for (const attribute of ["placeholder", "title", "aria-label", "alt"]) {
      const value = element.getAttribute(attribute);
      if (value) element.setAttribute(attribute, translated(value));
    }
  }

  function setLanguage(language) {
    if (!["en", "es"].includes(language)) return;
    localStorage.setItem("peti.language", language);
    document.documentElement.lang = language;
    document.title = language === "en" ? "PETi — Your companion. Our care." : "PETi — Tu compañero. Nuestro cuidado.";
    if (language === "en") queueMicrotask(() => apply());
  }

  setLanguage(localStorage.getItem("peti.language") || "es");
  new MutationObserver((records) => {
    if (document.documentElement.lang !== "en") return;
    for (const record of records) for (const node of record.addedNodes) if (node.nodeType === Node.ELEMENT_NODE) apply(node);
  }).observe(document.documentElement, { childList: true, subtree: true });
  window.PETI_I18N = { apply, setLanguage };
})();
