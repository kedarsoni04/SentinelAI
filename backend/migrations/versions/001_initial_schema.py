"""Initial schema - Phases 1 to 9

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-09 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'SECURITY_OPERATOR', 'VIEWER', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 2. cameras
    op.create_table(
        'cameras',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('location', sa.String(255), nullable=False),
        sa.Column('stream_url', sa.String(1024), nullable=True),
        sa.Column('source_type', sa.Enum('WEBCAM', 'RTSP', 'HTTP_STREAM', 'VIDEO_FILE', name='camerasourcetype'), nullable=False),
        sa.Column('status', sa.Enum('ONLINE', 'OFFLINE', 'UNKNOWN', name='camerastatus'), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_active', sa.DateTime(timezone=True), nullable=True),
    )

    # 3. analysis_jobs
    op.create_table(
        'analysis_jobs',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('camera_id', sa.String(36), sa.ForeignKey('cameras.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('source_path', sa.String(1024), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('status', sa.Enum('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED', name='jobstatus'), nullable=False),
        sa.Column('progress', sa.Float(), default=0.0, nullable=False),
        sa.Column('fps', sa.Float(), nullable=True),
        sa.Column('total_frames', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('resolution_width', sa.Integer(), nullable=True),
        sa.Column('resolution_height', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 4. analysis_results
    op.create_table(
        'analysis_results',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('analysis_job_id', sa.String(36), sa.ForeignKey('analysis_jobs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('frame_index', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('frame_path', sa.String(1024), nullable=False),
        sa.Column('thumbnail_path', sa.String(1024), nullable=False),
        sa.Column('annotated_frame_path', sa.String(1024), nullable=True),
        sa.Column('detection_count', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 5. tracked_objects
    op.create_table(
        'tracked_objects',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('analysis_job_id', sa.String(36), sa.ForeignKey('analysis_jobs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('track_id', sa.Integer(), nullable=False),
        sa.Column('class_name', sa.String(64), nullable=False),
        sa.Column('first_seen_timestamp', sa.Float(), nullable=False),
        sa.Column('last_seen_timestamp', sa.Float(), nullable=False),
        sa.Column('total_frames_tracked', sa.Integer(), default=1, nullable=False),
        sa.Column('duration_seconds', sa.Float(), default=0.0, nullable=False),
        sa.Column('net_displacement', sa.Float(), default=0.0, nullable=False),
        sa.Column('trajectory_distance', sa.Float(), default=0.0, nullable=False),
        sa.Column('is_stationary', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 6. track_points
    op.create_table(
        'track_points',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('tracked_object_id', sa.String(36), sa.ForeignKey('tracked_objects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('frame_index', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('x_center', sa.Float(), nullable=False),
        sa.Column('y_center', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 7. detections
    op.create_table(
        'detections',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('analysis_result_id', sa.String(36), sa.ForeignKey('analysis_results.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('class_name', sa.String(64), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('bbox_x', sa.Float(), nullable=False),
        sa.Column('bbox_y', sa.Float(), nullable=False),
        sa.Column('bbox_w', sa.Float(), nullable=False),
        sa.Column('bbox_h', sa.Float(), nullable=False),
        sa.Column('track_id', sa.Integer(), nullable=True),
        sa.Column('tracked_object_id', sa.String(36), sa.ForeignKey('tracked_objects.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 8. security_zones
    op.create_table(
        'security_zones',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('camera_id', sa.String(36), sa.ForeignKey('cameras.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('zone_type', sa.String(64), default='RESTRICTED', nullable=False),
        sa.Column('coordinates', sa.JSON(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 9. security_rules
    op.create_table(
        'security_rules',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('camera_id', sa.String(36), sa.ForeignKey('cameras.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('zone_id', sa.String(36), sa.ForeignKey('security_zones.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.Enum('INTRUSION', 'LOITERING', 'CROWD_DENSITY', 'UNUSUAL_MOVEMENT', name='securityruletype'), nullable=False),
        sa.Column('severity', sa.Enum('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='securityeventseverity'), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 10. security_events
    op.create_table(
        'security_events',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('analysis_job_id', sa.String(36), sa.ForeignKey('analysis_jobs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('camera_id', sa.String(36), sa.ForeignKey('cameras.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('rule_id', sa.String(36), sa.ForeignKey('security_rules.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('zone_id', sa.String(36), sa.ForeignKey('security_zones.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('event_type', sa.Enum('INTRUSION', 'LOITERING', 'CROWD_DENSITY', 'UNUSUAL_MOVEMENT', name='securityeventtype'), nullable=False),
        sa.Column('severity', sa.Enum('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='securityeventseverity_events'), nullable=False),
        sa.Column('status', sa.Enum('NEW', 'ACKNOWLEDGED', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE', name='securityeventstatus'), default='NEW', nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('start_timestamp', sa.Float(), nullable=False),
        sa.Column('end_timestamp', sa.Float(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('snapshot_frame_path', sa.String(1024), nullable=True),
        sa.Column('snapshot_thumbnail_path', sa.String(1024), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 11. incident_reports
    op.create_table(
        'incident_reports',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('analysis_job_id', sa.String(36), sa.ForeignKey('analysis_jobs.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('camera_id', sa.String(36), sa.ForeignKey('cameras.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('event_ids_json', sa.JSON(), nullable=False),
        sa.Column('ai_provider', sa.String(50), default='mock', nullable=False),
        sa.Column('ai_model', sa.String(100), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('timeline_json', sa.JSON(), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=True),
        sa.Column('risk_explanation', sa.Text(), nullable=True),
        sa.Column('recommendations_json', sa.JSON(), nullable=True),
        sa.Column('disclaimer', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), default='GENERATING', nullable=False, index=True),
        sa.Column('error_message', sa.String(1024), nullable=True),
        sa.Column('incident_status', sa.String(20), default='OPEN', nullable=False, index=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('incident_reports')
    op.drop_table('security_events')
    op.drop_table('security_rules')
    op.drop_table('security_zones')
    op.drop_table('detections')
    op.drop_table('track_points')
    op.drop_table('tracked_objects')
    op.drop_table('analysis_results')
    op.drop_table('analysis_jobs')
    op.drop_table('cameras')
    op.drop_table('users')
