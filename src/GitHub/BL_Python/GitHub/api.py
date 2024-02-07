from typing import Any, Literal, cast

from github import Auth
from github import Github as pygithub
from github.AuthenticatedUser import AuthenticatedUser
from github.GithubObject import NotSet, Opt
from github.NamedUser import NamedUser
from github.Organization import Organization
from github.Repository import Repository

GITHUB_API_BASE_URL = "https://api.github.com"


class GitHub:
    """
    Extends PyGithub with better organization API handling.
    """

    _client: pygithub

    def __init__(
        self, auth_token: str, default_api_url: str = GITHUB_API_BASE_URL
    ) -> None:
        auth = Auth.Token(auth_token)
        self._client = pygithub(base_url=default_api_url, auth=auth)
        super().__init__()

    def get_team(self, organization: Organization, team_name: str):
        """
        Get a team for an organization.
        """
        team = organization.get_team_by_slug(team_name)
        return team

    def add_collaborator(
        self,
        repository: Repository,
        collaborator: str | NamedUser,
        permission: Opt[str] = NotSet,
    ):
        """
        Add a user as a collaborator to a repository.
        """
        invitation = repository.add_to_collaborators(
            collaborator, permission=permission
        )
        return invitation

    def get_repository(
        self, repository_name: str, organization_name: str | None = None
    ):
        """
        Get a repository.
        If `organization_name` is supplied, this will get the repository `repository_name` from that organization's repositories.
        """
        if organization_name is None:
            return self._get_repository_for_user(repository_name)

        return self._get_repository_for_organization(repository_name, organization_name)

    def _get_repository_for_user(self, repository_name: str):
        user = self._client.get_user()
        return self._client.get_repo(f"{user.login}/{repository_name}")

    def _get_repository_for_organization(
        self, repository_name: str, organization_name: str
    ):
        ## repo = organization.get_repo(repository_name)
        ## can't use repo.organization because of this
        ## https://github.com/PyGithub/PyGithub/issues/1598
        repository = self._client.get_repo(f"{organization_name}/{repository_name}")
        organization: Organization = self._client.get_organization(organization_name)
        # fixes the PyGithub API URLs for working with the organiztion owning the repository
        cast(
            Any, repository._organization  # pyright: ignore[reportPrivateUsage]
        )._value = organization
        return repository

    def create_repository(
        self,
        name: str,
        description: str,
        organization_name: str | None = None,
        template_name: str | None = None,
        private: bool = True,
        visibility: Literal["private", "internal", "public"] | None = None,
    ):
        """
        Create a new repository.
        """
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
        # PyGitHub code does not allow "internal,"
        # so we do the same thing repository.edit does
        # to avoid the incorrect assertions.
        (
            _,
            data,
        ) = repository._requester.requestJsonAndCheck(  # pyright: ignore[reportPrivateUsage]
            "PATCH", repository.url, input={"visibility": visibility}
        )
        repository._useAttributes(data)  # pyright: ignore[reportPrivateUsage]
