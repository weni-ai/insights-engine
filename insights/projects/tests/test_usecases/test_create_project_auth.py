from django.test import TestCase

from insights.projects.usecases import InvalidProjectAuth
from insights.projects.usecases.auth_creation import (
    ProjectAuthCreationUseCase,
    ProjectAuthDTO,
)

from insights.projects.models import Project, ProjectAuth
from insights.users.models import User


class TestProjectAuthCreationUseCase(TestCase):
    def test_create_or_update_admin_auth(self):
        proj = Project.objects.create(name="Test Project")
        user = User.objects.create_user("test@user.com")
        role = 1

        auth = ProjectAuthCreationUseCase().create_permission(
            ProjectAuthDTO(project=str(proj.uuid), user=user.email, role=role)
        )
        self.assertEqual(auth.project, proj)
        self.assertEqual(auth.user, user)
        self.assertEqual(auth.role, 0)

    def test_bulk_create_admin_auth(self):
        proj = Project.objects.create(name="Test Project")
        self.assertEqual(proj.authorizations.count(), 0)
        ProjectAuthCreationUseCase().bulk_create(
            project=str(proj.uuid),
            authorizations=[
                {"user": "john.doe@weni.ai", "role": 1},
                {"user": "lina.lawson@weni.ai", "role": 1},
                {"user": "agent@weni.ai", "role": 0},
            ],
        )
        self.assertEqual(proj.authorizations.count(), 3)

    def test_bulk_create_admin_auth_with_conflict(self):
        proj = Project.objects.create(name="Test Project")
        user = User.objects.create_user("test@user.com")
        auth = ProjectAuth.objects.create(project=proj, user=user, role=1)

        self.assertEqual(proj.authorizations.count(), 1)
        ProjectAuthCreationUseCase().bulk_create(
            project=str(proj.uuid),
            authorizations=[
                {"user": auth.user.email, "role": 1},
                {"user": "lina.lawson@weni.ai", "role": 1},
                {"user": "agent@weni.ai", "role": 0},
            ],
        )
        self.assertEqual(proj.authorizations.count(), 3)

    def test_bulk_create_admin_auth_with_empty_list(self):
        proj = Project.objects.create(name="Test Project")
        ProjectAuthCreationUseCase().bulk_create(
            project=str(proj.uuid),
            authorizations=[],
        )
        self.assertEqual(proj.authorizations.count(), 0)

    def test_update_auth_create(self):
        proj = Project.objects.create(name="Test Project")
        user = User.objects.create_user("test@user.com")
        auth = ProjectAuth.objects.create(project=proj, user=user, role=1)
        role = 0
        usecase = ProjectAuthCreationUseCase()
        auth = usecase.create_permission(
            ProjectAuthDTO(
                project=str(auth.project.uuid), user=auth.user.email, role=role
            )
        )
        self.assertEqual(auth.role, role)

    def test_update_auth_update(self):
        proj = Project.objects.create(name="Test Project")
        user = User.objects.create_user("test@user.com")
        auth = ProjectAuth.objects.create(project=proj, user=user, role=1)
        role = 0
        usecase = ProjectAuthCreationUseCase()
        auth = usecase.update_permission(
            ProjectAuthDTO(
                project=str(auth.project.uuid), user=auth.user.email, role=role
            )
        )
        self.assertEqual(auth.role, role)

    def test_create_or_update_auth_create_user_create(self):
        project = Project.objects.create(name="Test Project")
        user = "user@inexistent.com"
        role = 1
        usecase = ProjectAuthCreationUseCase()
        auth = usecase.create_permission(
            ProjectAuthDTO(project=str(project.uuid), user=user, role=role)
        )
        self.assertEqual(auth.project, project)
        self.assertEqual(auth.user.email, user)
        self.assertEqual(auth.role, 0)

    def test_create_or_update_auth_create_user_update(self):
        project = Project.objects.create(name="Test Project")
        user = "user@inexistent.com"
        role = 1
        usecase = ProjectAuthCreationUseCase()
        auth = usecase.update_permission(
            ProjectAuthDTO(project=str(project.uuid), user=user, role=role)
        )
        self.assertEqual(auth.project, project)
        self.assertEqual(auth.user.email, user)
        self.assertEqual(auth.role, 0)

    def test_delete_auth(self):
        proj = Project.objects.create(name="Test Project")
        user = User.objects.create_user("test@user.com")
        auth = ProjectAuth.objects.create(project=proj, user=user, role=1)

        self.assertEqual(proj.authorizations.count(), 1)
        result = ProjectAuthCreationUseCase().delete_permission(
            ProjectAuthDTO(project=str(proj.uuid), user=auth.user.email, role=0)
        )
        self.assertIsNone(result)
        self.assertEqual(proj.authorizations.count(), 0)

    def test_delete_inexistent_user_auth(self):
        proj = Project.objects.create(name="Test Project")
        with self.assertRaises(InvalidProjectAuth):
            ProjectAuthCreationUseCase().delete_permission(
                ProjectAuthDTO(
                    project=str(proj.uuid), user="user@inexistent.com", role=0
                )
            )

    # Additional tests to achieve 100% coverage

    def test_role_mapping_with_role_3(self):
        """Test role_mapping method when role is 3 (should return 1)"""
        usecase = ProjectAuthCreationUseCase()
        result = usecase.role_mapping(3)
        self.assertEqual(result, 1)

    def test_role_mapping_with_role_0(self):
        """Test role_mapping method when role is 0 (should return 0)"""
        usecase = ProjectAuthCreationUseCase()
        result = usecase.role_mapping(0)
        self.assertEqual(result, 0)

    def test_role_mapping_with_role_1(self):
        """Test role_mapping method when role is 1 (should return 0)"""
        usecase = ProjectAuthCreationUseCase()
        result = usecase.role_mapping(1)
        self.assertEqual(result, 0)

    def test_get_project_method(self):
        """Test get_project method directly"""
        proj = Project.objects.create(name="Test Project")
        usecase = ProjectAuthCreationUseCase()
        project = usecase.get_project(str(proj.uuid))
        self.assertEqual(project, proj)

    def test_get_or_create_user_by_email_method(self):
        """Test get_or_create_user_by_email method directly"""
        usecase = ProjectAuthCreationUseCase()
        user, created = usecase.get_or_create_user_by_email("newuser@test.com")
        self.assertEqual(user.email, "newuser@test.com")
        self.assertTrue(created)

    def test_get_or_create_user_by_email_existing_user(self):
        """Test get_or_create_user_by_email method with existing user"""
        existing_user = User.objects.create_user("existing@test.com")
        usecase = ProjectAuthCreationUseCase()
        user, created = usecase.get_or_create_user_by_email(existing_user.email)
        self.assertEqual(user, existing_user)
        self.assertFalse(created)

    def test_create_permission_with_role_3(self):
        """Test create_permission with role 3 to cover role_mapping edge case"""
        proj = Project.objects.create(name="Test Project")
        usecase = ProjectAuthCreationUseCase()
        auth = usecase.create_permission(
            ProjectAuthDTO(project=str(proj.uuid), user="test@role3.com", role=3)
        )
        self.assertEqual(auth.role, 1)  # role_mapping(3) should return 1

    def test_bulk_create_with_role_3(self):
        """Test bulk_create with role 3 to cover role_mapping edge case"""
        proj = Project.objects.create(name="Test Project")
        self.assertEqual(proj.authorizations.count(), 0)
        ProjectAuthCreationUseCase().bulk_create(
            project=str(proj.uuid),
            authorizations=[
                {"user": "role3@test.com", "role": 3},
            ],
        )
        self.assertEqual(proj.authorizations.count(), 1)
        auth = proj.authorizations.first()
        self.assertEqual(auth.role, 1)  # role_mapping(3) should return 1

    def test_delete_permission_with_project_uuid_string(self):
        """Test delete_permission with project UUID as string to cover the get method"""
        proj = Project.objects.create(name="Test Project")
        user = User.objects.create_user("test@user.com")
        auth = ProjectAuth.objects.create(project=proj, user=user, role=1)

        self.assertEqual(proj.authorizations.count(), 1)

        # Test with project UUID as string (not Project object)
        ProjectAuthCreationUseCase().delete_permission(
            ProjectAuthDTO(project=str(proj.uuid), user=auth.user.email, role=0)
        )
        self.assertEqual(proj.authorizations.count(), 0)

    def test_delete_permission_with_user_email_string(self):
        """Test delete_permission with user email as string to cover the get method"""
        proj = Project.objects.create(name="Test Project")
        user = User.objects.create_user("test@user.com")
        auth = ProjectAuth.objects.create(project=proj, user=user, role=1)

        self.assertEqual(proj.authorizations.count(), 1)

        # Test with user email as string (not User object)
        ProjectAuthCreationUseCase().delete_permission(
            ProjectAuthDTO(project=str(proj.uuid), user=auth.user.email, role=0)
        )
        self.assertEqual(proj.authorizations.count(), 0)
