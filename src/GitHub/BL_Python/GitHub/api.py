from typing import Any, Literal, cast

from github import Auth, Github
from github.AuthenticatedUser import AuthenticatedUser
from github.NamedUser import NamedUser
from github.Organization import Organization
from github.Repository import Repository

GITHUB_API_BASE_URL = "https://api.github.com"


class GitHub:
    _client: Github

    def __init__(
        self, auth_token: str, default_api_url: str = GITHUB_API_BASE_URL
    ) -> None:
        auth = Auth.Token(auth_token)
        self._client = Github(base_url=default_api_url, auth=auth)
        super().__init__()

    def get_team(self, organization: Organization, team_name: str):
        # organization = self._client.get_organization(organization_name)
        team = organization.get_team_by_slug(team_name)
        return team

    def add_collaborator(self, repository: Repository, collaborator: str | NamedUser):
        return repository.add_to_collaborators(collaborator)

    def create_repository(
        self,
        name: str,
        description: str,
        organization_name: str | None = None,
        template_name: str | None = None,
        private: bool = True,
        visibility: Literal["private", "internal", "public"] | None = None,
    ):
        if organization_name is None:
            return self._create_repository_for_user(
                name,
                description=description,
                template_name=template_name,
                private=private,
            )
        return self._create_repository_for_organization(
            name,
            description=description,
            organization_name=organization_name,
            template_name=template_name,
            private=private,
            visibility=visibility,
        )

    def _create_repository_for_user(
        self,
        name: str,
        description: str,
        template_name: str | None = None,
        private: bool = True,
    ):
        user = cast(AuthenticatedUser, self._client.get_user())
        repository: Repository
        if template_name is None:
            # name, description=description, private=private
            repository = user.create_repo(name)
        else:
            template_repo = user.get_repo(template_name)
            repository = user.create_repo_from_template(
                name, repo=template_repo, description=description, private=private
            )
        return repository

    def _create_repository_for_organization(
        self,
        name: str,
        description: str,
        organization_name: str,
        template_name: str | None = None,
        private: bool = True,
        visibility: Literal["private", "internal", "public"] | None = None,
    ):
        organization = self._client.get_organization(organization_name)
        repository: Repository
        if template_name is None:
            repository = organization.create_repo(
                name, description=description, private=private
            )
        else:
            template_repo = organization.get_repo(template_name)
            repository = organization.create_repo_from_template(
                name, repo=template_repo, description=description, private=private
            )

        if visibility is not None:
            self._set_repository_visibility(repository, visibility)

        return repository

    def _set_repository_visibility(
        self,
        repository: Repository,
        visibility: Literal["private", "internal", "public"],
    ):
        # PyGitHub code does not allow "internal"
        # so we call the same code here instead
        # to avoid the incorrect assertions.
        (
            _,
            data,
        ) = repository._requester.requestJsonAndCheck(  # pyright: ignore[reportPrivateUsage]
            "PATCH", repository.url, input={"visibility": visibility}
        )
        repository._useAttributes(data)  # pyright: ignore[reportPrivateUsage]