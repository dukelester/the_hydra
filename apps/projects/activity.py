from apps.projects.models import Project, ProjectFollow, ProjectView

SESSION_RECENT = "recent_project_slugs"
SESSION_COMPARE = "compare_project_slugs"
MAX_RECENT = 5
MAX_COMPARE = 4


def record_project_view(request, project):
    if request.user.is_authenticated:
        ProjectView.objects.update_or_create(user=request.user, project=project)
        follow = ProjectFollow.objects.filter(user=request.user, project=project).first()
        if follow:
            mark_follow_seen(follow, project)
        return
    slugs = [slug for slug in request.session.get(SESSION_RECENT, []) if slug != project.slug]
    slugs.insert(0, project.slug)
    request.session[SESSION_RECENT] = slugs[:MAX_RECENT]


def recent_projects_for(request, limit=MAX_RECENT):
    if request.user.is_authenticated:
        views = (
            ProjectView.objects.filter(user=request.user)
            .select_related("project", "project__institution")
            .prefetch_related("project__evidence_items")[:limit]
        )
        projects = []
        for item in views:
            item.project.viewed_at = item.viewed_at
            projects.append(item.project)
        return projects
    slugs = request.session.get(SESSION_RECENT, [])[:limit]
    if not slugs:
        return []
    projects = {
        project.slug: project
        for project in Project.objects.select_related("institution")
        .prefetch_related("evidence_items")
        .filter(slug__in=slugs)
    }
    return [projects[slug] for slug in slugs if slug in projects]


def attach_coverage(projects):
    from apps.core.services.coverage import calculate_evidence_coverage

    for project in projects:
        project.coverage = calculate_evidence_coverage(project)
    return projects


def follow_for(user, project):
    if not user.is_authenticated:
        return None
    return ProjectFollow.objects.filter(user=user, project=project).first()


def _ensure_follow(user, project):
    follow, _created = ProjectFollow.objects.get_or_create(
        user=user,
        project=project,
        defaults={
            "last_seen_updated_at": project.updated_at,
            "last_seen_status": project.status,
        },
    )
    return follow


def toggle_tracked(user, project):
    follow = _ensure_follow(user, project)
    follow.is_tracked = not follow.is_tracked
    if not follow.is_tracked and not follow.is_favourite:
        follow.delete()
        return None
    follow.save(update_fields=["is_tracked"])
    return follow


def toggle_favourite(user, project):
    follow = _ensure_follow(user, project)
    follow.is_favourite = not follow.is_favourite
    if not follow.is_tracked and not follow.is_favourite:
        follow.delete()
        return None
    follow.save(update_fields=["is_favourite"])
    return follow


def mark_follow_seen(follow, project):
    follow.last_seen_updated_at = project.updated_at
    follow.last_seen_status = project.status
    follow.save(update_fields=["last_seen_updated_at", "last_seen_status"])


def tracked_follows(user):
    follows = list(
        ProjectFollow.objects.filter(user=user, is_tracked=True)
        .select_related("project", "project__institution")
        .prefetch_related("project__evidence_items")
    )
    for follow in follows:
        follow.record_updated = follow.has_record_update()
        follow.status_changed = follow.has_status_change()
        follow.needs_attention = follow.record_updated or follow.status_changed
    follows.sort(key=lambda item: (not item.needs_attention, item.project.name))
    return follows


def favourite_projects(user):
    return [
        follow.project
        for follow in ProjectFollow.objects.filter(user=user, is_favourite=True)
        .select_related("project", "project__institution")
        .prefetch_related("project__evidence_items")
    ]


def compare_slugs(request):
    slugs = request.session.get(SESSION_COMPARE, [])
    return [slug for slug in slugs if slug][:MAX_COMPARE]


def add_to_compare(request, project):
    slugs = compare_slugs(request)
    if project.slug in slugs:
        return slugs
    if len(slugs) >= MAX_COMPARE:
        slugs = slugs[-(MAX_COMPARE - 1) :]
    slugs.append(project.slug)
    request.session[SESSION_COMPARE] = slugs
    return slugs


def remove_from_compare(request, slug):
    slugs = [item for item in compare_slugs(request) if item != slug]
    request.session[SESSION_COMPARE] = slugs
    return slugs


def clear_compare(request):
    request.session[SESSION_COMPARE] = []
