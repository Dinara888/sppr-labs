"""Модуль обработки: извлечение ключевых данных из JSON-ответа Wolfram|Alpha."""

# Идентификаторы pod'ов, в которых обычно находится основной ответ
PRIMARY_POD_IDS = ("Result", "IndefiniteIntegral", "Solution", "Value",
                   "DecimalApproximation", "Derivative")


def _pod_text(pod: dict) -> str:
    """Собирает текст всех подблоков (subpods) одного pod'а."""
    parts = [sp.get("plaintext", "").strip() for sp in pod.get("subpods", [])]
    return "\n".join(p for p in parts if p)


def extract(query_text: str, category: str, result: dict) -> dict:
    """Возвращает словарь с ключевыми данными ответа."""
    pods = result.get("pods", []) or []
    extracted = {
        "category": category,
        "query": query_text,
        "success": bool(result.get("success")),
        "interpretation": "",
        "answer": "",
        "pods": [],
    }
    for pod in pods:
        text = _pod_text(pod)
        if not text:
            continue
        extracted["pods"].append({"title": pod.get("title", ""), "text": text})
        if pod.get("id") == "Input":
            extracted["interpretation"] = text
        # Основной ответ: pod с флагом primary или с типичным id
        if not extracted["answer"] and (pod.get("primary") or pod.get("id") in PRIMARY_POD_IDS):
            extracted["answer"] = text

    # Если primary-pod не найден, берём первый содержательный после Input
    if not extracted["answer"]:
        for p in extracted["pods"]:
            if p["title"].lower() not in ("input", "input interpretation"):
                extracted["answer"] = p["text"]
                break

    if not extracted["success"] and not extracted["answer"]:
        tips = result.get("tips")
        extracted["answer"] = "Wolfram|Alpha не смог интерпретировать запрос" + (f" ({tips})" if tips else "")
    return extracted


def format_readable(item: dict, index: int) -> str:
    """Удобочитаемое представление результата для консоли и текстового файла."""
    lines = [
        "=" * 70,
        f"{index}. [{item['category']}] {item['query']}",
        "-" * 70,
    ]
    if item.get("interpretation"):
        lines.append(f"Интерпретация: {item['interpretation']}")
    lines.append(f"Ответ: {item['answer'] or '-'}")
    if item.get("error"):
        lines.append(f"Ошибка: {item['error']}")
    return "\n".join(lines)
