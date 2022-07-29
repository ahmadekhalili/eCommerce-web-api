from django.contrib.admin.templatetags.admin_list import result_headers, items_for_result, ResultList, result_hidden_fields
from django.contrib.admin.templatetags.base import InclusionAdminNode
from django.template import Library

register = Library()


def results(cl):
    if cl.formset:
        for res, form in zip(cl.result_list, cl.formset.forms):
            yield ResultList(form, items_for_result(cl, res, form))
    else:        
        results_pack = {10: [], 9: [], 8: [], 7: [], 6: [], 5: [], 4: [], 3: [], 2: [], 1: []} if cl.result_list else {}
        for res in cl.result_list.select_related('filterr'):
            results_pack[res.filterr.group] += [ResultList(None, items_for_result(cl, res, None))]
        results_list = [results_pack[key] for key in results_pack if results_pack[key]]
        for results in results_list:
            yield results


def result_list(cl):
    """
    Display the headers and data list together.
    """
    headers = list(result_headers(cl))
    num_sorted_fields = 0
    for h in headers:
        if h["sortable"] and h["sorted"]:
            num_sorted_fields += 1
    return {
        "cl": cl,
        "result_hidden_fields": list(result_hidden_fields(cl)),
        "result_headers": headers,
        "num_sorted_fields": num_sorted_fields,
        "results_list": list(results(cl)),
    }


@register.tag(name="result_list")
def result_list_tag(parser, token):
    return InclusionAdminNode(
        parser,
        token,
        func=result_list,
        template_name="change_list_results.html",
        takes_context=False,
    )
