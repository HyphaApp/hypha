from .payment import (
    ChangeInvoiceStatusView,
    CreateInvoiceView,
    DeleteInvoiceView,
    EditInvoiceView,
    InvoiceListView,
    InvoicePrivateMedia,
    InvoiceView,
)
from .project import (
    AdminProjectDetailView,
    ApplicantProjectDetailView,
    ApproveContractView,
    BaseProjectDetailView,
    ContractPrivateMediaView,
    CreateApprovalView,
    ProjectApprovalEditView,
    ProjectDetailPDFView,
    ProjectDetailSimplifiedView,
    ProjectDetailView,
    ProjectListView,
    ProjectOverviewView,
    ProjectPrivateMediaView,
    RejectionView,
    RemoveDocumentView,
    SelectDocumentView,
    SendForApprovalView,
    UpdateLeadView,
    UploadContractView,
    UploadDocumentView,
)
from .report import (
    ReportDetailView,
    ReportFrequencyUpdate,
    ReportListView,
    ReportPrivateMedia,
    ReportSkipView,
    ReportUpdateView,
)
from .vendor import CreateVendorView, VendorDetailView, VendorPrivateMediaView

__all__ = [
    'ChangeInvoiceStatusView',
    'SendForApprovalView',
    'CreateApprovalView',
    'RejectionView',
    'UploadDocumentView',
    'RemoveDocumentView',
    'SelectDocumentView',
    'UpdateLeadView',
    'ApproveContractView',
    'UploadContractView',
    'BaseProjectDetailView',
    'AdminProjectDetailView',
    'ApplicantProjectDetailView',
    'ProjectDetailView',
    'ProjectPrivateMediaView',
    'ContractPrivateMediaView',
    'ProjectDetailSimplifiedView',
    'ProjectDetailPDFView',
    'ProjectApprovalEditView',
    'ProjectListView',
    'ProjectOverviewView',
    'ReportDetailView',
    'ReportUpdateView',
    'ReportPrivateMedia',
    'ReportSkipView',
    'ReportFrequencyUpdate',
    'ReportListView',
    'CreateVendorView',
    'VendorDetailView',
    'VendorPrivateMediaView',
    'CreateInvoiceView',
    'InvoiceListView',
    'InvoiceView',
    'EditInvoiceView',
    'DeleteInvoiceView',
    'InvoicePrivateMedia',
]
