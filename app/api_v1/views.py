from flask import jsonify, request, current_app,abort, make_response
from . import api
from app import models, db
from flask_login import login_required,current_user
from app.utils.decorators import roles_required
from app.utils.jquery_filters import Filter
from app.utils.misc import project_creation
from sqlalchemy import func
import arrow

@api.route('/health', methods=['GET'])
def get_health():
    return jsonify({"message":"ok"})

@api.route('/projects/<int:id>', methods=['GET'])
@login_required
def project(id):
    project = models.Project.query.get(id)
    return jsonify(project.as_dict())

@api.route('/policies/<int:id>', methods=['GET'])
@login_required
def policy(id):
    policy = models.Policy.query.get(id)
    return jsonify(policy.as_dict())

@api.route('/policies/<int:id>', methods=['PUT'])
@roles_required("admin")
def update_policy(id):
    data = request.get_json()
    policy = models.Policy.query.get(id)
    policy.name = data["name"]
    policy.description = data["description"]
    policy.template = data["template"]
    policy.content = data["content"]
    db.session.commit()
    return jsonify(policy.as_dict())

@api.route('/frameworks/<int:id>', methods=['GET'])
@login_required
def get_framework(id):
    framework = models.Framework.query.get(id)
    return jsonify(framework.as_dict())

@api.route('/frameworks', methods=['POST'])
@roles_required("admin")
def add_framework():
    payload = request.get_json()
    framework = models.Framework(name=payload["name"],
        description=payload.get("description"),
        reference_link=payload.get("link"))
    db.session.add(framework)
    db.session.commit()
    return jsonify(framework.as_dict())

@api.route('/evidence/<int:id>', methods=['GET'])
@roles_required("admin")
def get_evidence(id):
    evidence = models.Evidence.query.get(id)
    return jsonify(evidence.as_dict())

@api.route('/evidence', methods=['POST'])
@roles_required("admin")
def add_evidence():
    payload = request.get_json()
    evidence = models.Evidence(name=payload["name"],
        description=payload["description"],content=payload["content"])
    db.session.add(evidence)
    db.session.commit()
    return jsonify(evidence.as_dict())

@api.route('/evidence/<int:id>', methods=['PUT'])
@roles_required("admin")
def update_evidence(id):
    payload = request.get_json()
    evidence = models.Evidence.query.get(id)
    evidence.name = payload["name"]
    evidence.description = payload["description"]
    evidence.content = payload["content"]
    db.session.commit()
    return jsonify(evidence.as_dict())

@api.route('/evidence/<int:id>/files', methods=["GET"])
@roles_required("admin")
def evidence_files_list(id):
    evidence_files = models.EvidenceFile.query.filter(models.EvidenceFile.evidence_id==id).all()
    file_ids = [i.id for i in evidence_files]
    return jsonify({"files":file_ids})

@api.route('/evidence/<int:id>/add_file', methods=["POST"])
@roles_required("admin")
def evidence_files_add(id):
    file_data = request.form.get("file")
    filename = request.form.get("filename")
    evidence_file = models.EvidenceFile(file=file_data, name=filename, evidence_id=id)
    db.session.add(evidence_file)
    db.session.commit()
    return jsonify({"message":"ok"})

@api.route('/evidence/file/<int:id>', methods=["GET"])
@roles_required("admin")
def evidence_dowload_file_by_id(id):
    file_data = models.EvidenceFile.query.get(id)
    if(file_data):
        response = make_response(file_data.file)
        response.headers.set('Content-Disposition', 'attachment', filename=file_data.name)
        response.headers.set("Content-Type","binary/octact-stream")
        return response
    return jsonify({"message":"file not found"}), 404

@api.route('/evidence/file/<int:id>', methods=["DELETE"])
@roles_required("admin")
def evidence_file_delete(id):
    file_d = models.EvidenceFile.query.get(id)
    if file_d:
        db.session.delete(file_d)
        db.session.commit()
        return jsonify({"message":"ok"})
    return jsonify({"message":"file not found"}), 404

@api.route('/evidence/<int:id>', methods=['DELETE'])
@roles_required("admin")
def delete_evidence(id):
    evidence = models.Evidence.query.get(id)
    db.session.delete(evidence)
    db.session.commit()
    return jsonify({"message":"ok"})

@api.route('/evidence/<int:id>/controls', methods=['PUT'])
@roles_required("admin")
def add_evidence_to_controls(id):
    payload = request.get_json()
    evidence = models.Evidence.query.get(id)
    evidence.associate_with_controls(payload)
    return jsonify({"message":"ok"})

@api.route('/policies', methods=['POST'])
@roles_required("admin")
def add_policy():
    payload = request.get_json()
    policy = models.Policy(name=payload["name"],
        description=payload["description"])
    db.session.add(policy)
    db.session.commit()
    return jsonify(policy.as_dict())

@api.route('/policies/<int:id>', methods=['DELETE'])
@roles_required("admin")
def delete_policy(id):
    policy = models.Policy.query.get(id)
    policy.visible = False
    db.session.commit()
    return jsonify({"message":"ok"})

@api.route('/controls/<int:id>', methods=['DELETE'])
@roles_required("admin")
def delete_control(id):
    control = models.Control.query.get(id)
    control.visible = False
    db.session.commit()
    return jsonify({"message":"ok"})

@api.route('/controls', methods=['POST'])
@roles_required("admin")
def create_control():
    payload = request.get_json()
    control = models.Control.create(payload),
    return jsonify({"message":"ok"})

@api.route('/controls/<int:id>', methods=['GET'])
@login_required
def control(id):
    control = models.Control.query.get(id)
    return jsonify(control.as_dict())

@api.route('/projects', methods=['POST'])
@roles_required("admin")
def create_project():
    payload = request.get_json()
    result = project_creation(payload, current_user)
    if not result:
        return jsonify({"message":"failed to create project"}),400
    return jsonify({"message":"project created"})

@api.route('/projects/subcontrols', methods=['GET'])
@login_required
def get_subcontrols_in_projects():
    data = []
    for subcontrol in models.ProjectSubControl.query.all():
        data.append(subcontrol.as_dict())
    return jsonify(data)

@api.route('/projects/<int:id>/controls', methods=['GET'])
@login_required
def get_controls_for_project(id):
    data = []
    project = models.Project.query.get(id)
    for control in project.controls.all():
        for subcontrol in control.subcontrols.all():
            data.append(subcontrol.as_dict(include_evidence=True))
    return jsonify(data)

@api.route('/projects/<int:id>/policies/<int:pid>', methods=['GET'])
@login_required
def get_policy_for_project(id, pid):
    policy = models.ProjectPolicy.query.get(pid)
    return jsonify(policy.as_dict())

@api.route('/projects/<int:id>/policies/<int:pid>', methods=['PUT'])
@roles_required("admin")
def update_policy_for_project(id, pid):
    data = request.get_json()
    policy = models.ProjectPolicy.query.get(pid)
    policy.name = data["name"]
    policy.description = data["description"]
    policy.template = data["template"]
    policy.content = data["content"]
    policy.public_viewable = data["public"]
    db.session.commit()
    return jsonify(policy.as_dict())

@api.route('/projects/<int:id>/policies/<int:pid>', methods=['DELETE'])
@roles_required("admin")
def delete_policy_for_project(id, pid):
    project = models.Project.query.get(id)
    project.remove_policy(pid)
    return jsonify({"message":"policy removed"})

@api.route('/policies/<int:id>/controls/<int:cid>', methods=['PUT'])
@roles_required("admin")
def update_controls_for_policy(id, cid):
    policy = models.Policy.query.get(id)
    policy.add_control(cid)
    return jsonify({"message":"ok"})

@api.route('/policies/<int:id>/controls/<int:cid>', methods=['DELETE'])
@roles_required("admin")
def delete_controls_for_policy(id, cid):
    policy = models.Policy.query.get(id)
    if control := policy.has_control(cid):
        db.session.delete(control)
        db.session.commit()
    return jsonify({"message":"ok"})

@api.route('/projects/<int:id>/policies/<int:pid>/controls/<int:cid>', methods=['PUT'])
@roles_required("admin")
def update_policy_controls_for_project(id, pid, cid):
    policy = models.ProjectPolicy.query.get(pid)
    policy.add_control(cid)
    return jsonify({"message":"ok"})

@api.route('/projects/<int:id>/policies/<int:pid>/controls/<int:cid>', methods=['DELETE'])
@roles_required("admin")
def delete_policy_controls_for_project(id, pid, cid):
    policy = models.ProjectPolicy.query.get(pid)
    if control := policy.has_control(cid):
        db.session.delete(control)
        db.session.commit()
    return jsonify({"message":"ok"})

@api.route('/projects/<int:id>/controls/<int:cid>', methods=['GET'])
@login_required
def get_control_for_project(id, cid):
    control = models.ProjectControl.query.get(cid)
    return jsonify(control.as_dict(include_subcontrols=True))

@api.route('/projects/<int:id>/controls/<int:cid>', methods=['DELETE'])
@login_required
def remove_control_from_project(id, cid):
    project = models.Project.query.get(id)
    project.remove_control(cid)
    return jsonify({"message":"ok"})

@api.route('/policies/<int:pid>/projects/<int:id>', methods=['PUT'])
@roles_required("admin")
def add_policy_to_project(pid, id):
    policy = models.Policy.query.get(pid)
    project = models.Project.query.get(id)
    project.add_policy(policy)
    return jsonify(policy.as_dict())

@api.route('/controls/<int:cid>/projects/<int:id>', methods=['PUT'])
@roles_required("admin")
def add_control_to_project(cid, id):
    control = models.Control.query.get(cid)
    project = models.Project.query.get(id)
    project.add_control(control)
    return jsonify(control.as_dict())

@api.route('/query/controls', methods=['GET','POST'])
@login_required
def query_controls():
    """
    return query results for dt table
    """
    payload = request.get_json()
    include_cols = request.args.get("columns", "no")
    _filter = Filter(models, current_app.db.session.query(),tables=["controls"])
    data = _filter.handle_request(
        payload,
        default_filter={"condition":"OR","rules":[{"field":"controls.id","operator":"is_not_null"}]},
        default_fields=["id", "criteria", "control_ref"]
    )
    if include_cols == "no":
        data.pop("columns", None)
    return jsonify(data)

@api.route('/project-controls/<int:cid>/subcontrols/<int:sid>', methods=['PUT'])
@roles_required("admin")
def update_subcontrols_in_control_for_project(cid, sid):
    payload = request.get_json()
    sub = models.ProjectSubControl.query.get(sid)
    sub.is_applicable = payload["applicable"]
    sub.implemented = payload["implemented"]
    sub.notes = payload["notes"]
    sub.auditor_feedback = payload["feedback"]
    sub.set_evidence(payload["evidence"])
    db.session.commit()
    return jsonify({"message":"ok"})

@api.route('/project-controls/<int:cid>/applicability', methods=['PUT'])
@roles_required("admin")
def set_applicability_of_control_for_project(cid):
    payload = request.get_json()
    control = models.ProjectControl.query.get(cid)
    control.set_applicability(payload["applicable"])
    return jsonify({"message":"ok"})

@api.route('/tags/<int:id>', methods=['DELETE'])
@roles_required("admin")
def delete_tag(id):
    tag = models.Tag.query.get(id)
    if not tag:
        return jsonify({"message": "not found"}), 404
    db.session.delete(tag)
    db.session.commit()
    return jsonify({"message": "ok"})

@api.route('/labels/<int:id>', methods=['DELETE'])
@roles_required("admin")
def delete_label(id):
    label = models.PolicyLabel.query.get(id)
    if not label:
        return jsonify({"message": "not found"}), 404
    db.session.delete(label)
    db.session.commit()
    return jsonify({"message": "ok"})

@api.route('/charts/project-summaries', methods=['GET'])
@login_required
def charts_get_project_summaries():
    data = {
        "categories":[],
        "controls":[],
        "policies":[],
        "complete":[],
        "not_implemented":[],
        "missing_evidence":[],
    }
    for project in models.Project.query.order_by(models.Project.id.desc()).limit(5).all():
        data["categories"].append(project.name)
        data["controls"].append(project.controls.count())
        data["policies"].append(project.policies.count())
        data["complete"].append(len(project.completed_controls()))
        data["not_implemented"].append(len(project.completed_controls()))
        data["missing_evidence"].append(len(project.missing_evidence_controls()))
    return jsonify(data)

@api.route('/charts/tenant-summary', methods=['GET'])
@login_required
def charts_get_tenant_summary():
    data = {
        "categories":["Projects","Controls","Policies","Subcontrols", "Users"],
        "data":[]
    }
    data["data"].append(models.Project.query.count())
    data["data"].append(models.Control.query.count())
    data["data"].append(models.Policy.query.count())
    data["data"].append(models.SubControl.query.count())
    data["data"].append(models.User.query.count())
    return jsonify(data)

@api.route('/charts/controls-by-framework', methods=['GET'])
@login_required
def charts_get_controls_by_framework():
    data = {
        "categories":[],
        "data":[]
    }
    for control in models.Framework.query.with_entities(models.Framework.name,func.count(models.Framework.name)).group_by(models.Framework.name).all():
        data["categories"].append(control[0])
        data["data"].append(control[1])
    return jsonify(data)

@api.route('/charts/controls-by-category', methods=['GET'])
@login_required
def charts_get_control_by_category():
    data = {
        "categories":[],
        "data":[]
    }
    for control in models.Control.query.with_entities(models.Control.category,func.count(models.Control.category)).group_by(models.Control.category).all():
        data["categories"].append(control[0])
        data["data"].append(control[1])
    return jsonify(data)

@api.route('/charts/controls-by-subcategory', methods=['GET'])
@login_required
def charts_get_control_by_subcategory():
    data = {
        "categories":[],
        "data":[]
    }
    for control in models.Control.query.with_entities(models.Control.subcategory,func.count(models.Control.subcategory)).group_by(models.Control.subcategory).all():
        data["categories"].append(control[0])
        data["data"].append(control[1])
    return jsonify(data)
