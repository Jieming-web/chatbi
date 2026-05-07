import re

from langchain_core.messages import HumanMessage

from .prompts import SQL_SYSTEM_PROMPT, FEW_SHOT_EXAMPLES
from .schema_formatter import format_schema, format_roles


def _extract_sql(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:sql)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


class SQLBuilder:
    def __init__(self, llm):
        self.llm = llm

    def build(
        self,
        normalized_query: str,
        schema_context: dict,
        roles: dict,
        error: str = "",
        prev_sql: str = "",
    ) -> str:
        schema_text = format_schema(schema_context)
        roles_text = format_roles(roles)

        system_content = SQL_SYSTEM_PROMPT.format(
            schema_context=schema_text,
            few_shot=FEW_SHOT_EXAMPLES,
        )

        if error:
            user_content = (
                f"Question: {normalized_query}\n"
                + (f"\nIntent analysis:\n{roles_text}\n" if roles_text else "")
                + f"\nThe previously generated SQL failed to execute:\n{prev_sql}\n"
                f"Error message: {error}\n\n"
                "Please fix the SQL. Output SQL only, with no explanation:"
            )
        else:
            user_content = (
                f"Question: {normalized_query}\n"
                + (f"\nIntent analysis:\n{roles_text}\n" if roles_text else "")
                + "\nSQL:"
            )

        response = self.llm.invoke([
            HumanMessage(content=system_content + "\n\n" + user_content)
        ])
        return _extract_sql(response.content)
