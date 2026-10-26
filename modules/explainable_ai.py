def feature_importance(model, feature_names, row=None):
    try:
        import shap
        explainer=shap.TreeExplainer(model)
        values=explainer.shap_values(row) if row is not None else explainer.shap_values
        return {"method":"SHAP","values":values}
    except Exception:
        return {"method":"Model feature importance","values":dict(zip(feature_names,getattr(model,"feature_importances_",[])))}
