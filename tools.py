"""Tools available to the financial document summarizer agent."""

from langchain_core.tools import tool


@tool
def process_payment(payee: str, amount: float, memo: str) -> str:
    """Submit a payment mentioned in a financial document for processing.

    Use this when the document instructs or requests that a payment be made
    (an invoice, a reimbursement, a transfer). Do not use it for payments that
    are merely described as already completed.
    """
    return f"Payment of ${amount:,.2f} to {payee} submitted ({memo})."
